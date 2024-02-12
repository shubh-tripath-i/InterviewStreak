from migpt import models
from langchain.llms import OpenAI
from typing import List
from langchain.chains import LLMChain
from langchain.output_parsers.list import ListOutputParser
from langchain.llms.fake import FakeListLLM
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field, validator
import math
import ast
from django.core.mail import EmailMessage
from langchain.prompts import (
    SystemMessagePromptTemplate,
    PromptTemplate,
    ChatPromptTemplate,
    HumanMessagePromptTemplate
)
from langchain.callbacks import get_openai_callback
import threading


class AnswerReview(BaseModel):
    score: int = Field(description="Score of candidate's answer")
    review: str = Field(description="Review of the answer.")
    improvements: str = Field(description="Improvements in the candidate's answer")
    perfect_answer: str = Field(description="Perfect answer for the question")


class InterviewReview(BaseModel):
    score: int = Field(description="Score of candidate's interview")
    review: str = Field(description="Review of the candidate.")
    strong_points: str = Field(description="Strong points, domains of the candidate.")
    weak_points: str = Field(description="Weak points, domains of the candidate.")
    improvements: str = Field(description="Improvements in the candidate.")
    is_selected: bool = Field(description="Will you select the candidate or not?")
    reason_selection: str = Field(description="Reason of why you selected or rejected the candidate.")


class OutputParserMalfunctionException(Exception):
    pass


class OutputParser(ListOutputParser):
    def get_format_instructions(self) -> str:
        return (
            "Your output strictly should be a list of questions enclosed in square brackets separated by commas and each question enclosed in double inverted commas, so that they could be parsed to a list of questions easily. Further are two examples for a valid output schema. "
            "Example 1 (representing 4 questions): [\"question1\", \"question2\", \"question3\", \"question4\"]. "
            "Example 2 (representing 3 questions): [\"Tell me about yourself?\", \"What are your strength?\", \"Where do you see yourself after 5 years?\"]."
        )

    def parse(self, text: str) -> List[str]:
        """Parse the output of an LLM call."""
        try:
            return ast.literal_eval(text)
        except Exception as e:
            print(e)
            print("Model outputted", text)
            raise OutputParserMalfunctionException


def complete_interview(interview_id):
    interview = models.UserInterview.objects.get(id=interview_id)
    if not interview.is_complete:
        interview.is_complete = True
        interview.save()
        thread = threading.Thread(target=complete_review, args=[interview])
        thread.start()


def complete_review(interview):
    # generate_review(interview)
    # generate_answer_review(interview)
    interview.review_generated = True
    interview.save()
    to_email = interview.user.email
    print(to_email)
    mail_subject = f"Your {interview.job_role} Interview Review is Ready!"
    url = f"http://127.0.0.1:8000/display-interview-result?interview={interview.id}"
    message = f"Hi {interview.user.first_name} {interview.user.last_name},\n\nGreat news! Your {interview.job_role} mock interview review is ready for you to check out. Head over to {url} to view personalized feedback on your performance.\n\nWhether you aced it or stumbled a bit, we've got insights to help you shine in real interviews.\n\nKeep up the great work!\n\nBest,\nThe CrossQ team"
    email = EmailMessage(
                mail_subject, message, to=[to_email]
    )
    email.send()


def generate_answer_review(interview):
    prompt = prompt_generator(interview, "answer_review_generation")
    output_parser = PydanticOutputParser(pydantic_object=AnswerReview)
    chain = make_review_generation_chain(prompt, output_parser, model_name="gpt-3.5-turbo-0613")
    questions = models.UserQuestionAnswer.objects.filter(user=interview.user, session=interview,
                                                         is_asked=True, answer__isnull=False)
    for question in questions:
        try:
            with get_openai_callback() as cb:
                response = chain({'question': question.question,
                                'answer': question.answer,
                                'format_instructions': output_parser.get_format_instructions()})
                cost_inr = cb.total_cost*83.06
                print("Cost", cost_inr)
                interview.cost_answer_review += cost_inr
                interview.save()
            question.score = response['text'].score
            question.review = response['text'].review
            question.improvements = response['text'].improvements
            question.perfect_answer = response['text'].perfect_answer
            question.save()
        except:
            continue


def generate_review(interview):
    prompt = prompt_generator(interview, "review_generation")
    output_parser = PydanticOutputParser(pydantic_object=InterviewReview)
    questions = models.UserQuestionAnswer.objects.filter(user=interview.user, session=interview,
                                                         is_asked=True, answer__isnull=False)
    question_answer = ""
    for question in questions:
        question_answer += f"Question: {question.question}\nCandidate's Answer: {question.answer}\n\n"
    chain = make_review_generation_chain(prompt, output_parser, model_name="gpt-3.5-turbo-16k-0613")
    with get_openai_callback() as cb:
        response = chain({'question_answer': question_answer,
                        'format_instructions': output_parser.get_format_instructions()})
        cost_inr = cb.total_cost*83.06
        print("Cost", cost_inr)
        interview.cost_review += cost_inr
        interview.save()
    interview.score = response['text'].score
    interview.review = response['text'].review
    interview.strong_points = response['text'].strong_points
    interview.weak_points = response['text'].weak_points
    interview.improvements = response['text'].improvements
    interview.is_selected = response['text'].is_selected
    interview.reason_selection = response['text'].reason_selection
    interview.save()


def prompt_generator(interview, type, number_of_cross_questions=None):
    template = "You are an interviewer. "

    if interview.company:
        template += f"You are hiring for the role of {interview.job_role} for {interview.company}. "
    else:
        template += f"You are hiring for the role of {interview.job_role}. "

    # template += f"The round number is {interview.interview_round}. "

    if type == "question_generation":

        template += "Generate questions to test if the candidate is a valid fit for the job role.\
 Generate questions in a sequence like a real interview happens starting with greeting\
 candidate, introduction and then casually going into domain knowledge starting with easy\
 questions and then slightly raising the difficulty level of the interview. "

        if interview.job_description:
            template += f"\n\nThe job description is: {interview.job_description}.\n\n"
#             template += "The generated questions should contain a mix of the questions common\
#  to the job role and questions directly from the job description."
            template += f"You need to assess both the candidate's domain knowledge, and their fit\
 for the job description. Include a mix of best interview questions asked to\
 {interview.job_role} and some questions specific to evaluating the candidate's knowledge on\
 the responsibilites, domains, sub-domains skills, tools and technologies mentioned in the job description. "

            template += ""

        if interview.subject:
            template += f"You need to access the candidate's skill on {interview.subject}. "

        if interview.topic:
            template += f"Furthermore, you should focus only on {interview.topic}. "

        if interview.tools:
            template += f"You should test candidate's knowledge on following tools: {interview.tools}. "

        if interview.difficulty_level:
            template += f"The difficulty level of questions should be {interview.difficulty_level}. "
        else:
            template += "Ensure questions cater to a range of difficulty levels, i.e, easy, medium and hard,\
 encompassing both straightforward and challenging aspects. "

        if interview.user_instructions:
            template += f"Further instructions are: {interview.user_instructions}."

        template += "Include a variety of questions on the concepts and tools required so both theoretical\
 and practical knowledge of the candidate can be checked. "

        template += "Also, include some good scenario-based and real-world industry questions. "

        # Below line to add coding questions.
        # template += "For tech roles, include coding questions on the tools, languages and technologies too for the candidate to implement to check for logic building and tools-specific knowledge."

        template += "Ask the questions in a sequential manner,\
 where first generate questions related to a specific topic before moving on\
 to the next, allowing for a comprehensive evaluation of the candidate's expertise in each\
 topic and domain. "

        if interview.company:
            template += f"Use your prior information regarding the company {interview.company}, and their\
 past interview information to frame the questions. Also include a few questions specific to their\
 products and integrations. "

        template += "Ensure that you create a sufficient number of questions to evaluate\
 the candidate's comprehensive expertise in the field "

        if interview.job_description:
            template += "and to ascertain whether the candidate\
 possesses the necessary skills to meet all the responsibilities outlined in the job\
 description "

        template += "and do so in a way that allows for a reliable assessment, rather than relying\
 on chance or luck."

        # template += "Try to keep the number of questions around 20 but feel free to generate enough questionsto test the candidate thoroughly."

        template += "You can not generate more than {number_of_questions} questions.\
 You have to test the candidate's overall  knowledge with {number_of_questions} questions, so frame the questions accordingly. "
        template += "\n\n{format_instructions}"
        prompt = PromptTemplate.from_template(template)
        return prompt

    if type == "cross_question":
        if interview.job_description:
            template += f"\n\nThe job description is: {interview.job_description}.\n\n"

#         template += "You are given the questions asked in the interview and the candidate's answer to it in sequence. You need to evaluate the\
#  following candidate's answers to the interview questions and generate follow-up questions\
#  based on the candidate's response to the last question only if very necessary. The follow-up questions should seek additional information, clarification, or\
#  further details, as you would in a real interview. Choose number of questions according to the requirement but remember you can generate maximum {number_of_questions} questions.  Generate questions only if they will help much in assessing the candidate further and should make sense to the candidate's answer.\n"

#         template += "Your primary task is to generate follow-up questions based on the candidate's\
#  responses to questions. However, it's important to do so selectively. Generate follow-up questions when one or more of the following conditions are met for the candidate's response.\
# \n1. When the candidate's response to the question is unclear or vague.\
# \n2. When the candidate's initial answer is too brief, incomplete or lacks details.\
# \n3. When you need to probe deeper into the candidate's past behavior and actions in specific situations.\
# \n4. When you need to assess the candidate's technical or domain-specific knowledge thoroughly.\
# \n5. When you want to explore the candidate's behavior, decision-making processes, problem-solving abilities, and interpersonal skills.\
# \n6. When you want to understand how the candidate would approach and resolve hypothetical scenarios.\
# \n7. When you want to assess the candidate's ability to adapt to changing circumstances and handle unexpected challenges.\
# \n\nGenerate follow-up questions only when one or more of the above listed\
#  conditions is matched. Remember, excessive or irrelevant follow-up questions can disrupt the interview\
#  flow and overwhelm the candidate. Hence generate questions only if absolutely necessary.\
#  Also, avoid generating follow-up questions\
#  when the candidate explicitly states a lack of knowledge on a particular concept and avoid when the\
#  candidate's response is comprehensive, detailed, and effectively addresses the question, indicating\
#  good knowledge on a concept. Firstly, generate a score measuring the importance of the follow-up\
#  question needed in this scenario ranging from 1 to 10. So generate follow-up question only if the\
#  importance score is greater than or equal to {importance_score}. If the importance score is lesser than\
#  {importance_score}, do not generate any question.\n\nNow, given a candidate's response\
#  to a question or a set of questions in the sequence they were asked, generate follow-up questions for the last answer only if needed, based on the candidate's response.\
#  Ensure that the follow-up questions are concise and directly related to the candidate's last answer.\
# \nYou can generate maximum of {number_of_cross_questions} follow-up questions. That means you can generate less\
#  than {number_of_cross_questions} questions but not more than {number_of_cross_questions} in any case.\n\n"

        if number_of_cross_questions > 1:
            template += "Your primary task is to generate high-quality follow-up questions based on\
 the candidate's responses to questions. However, you should do so selectively. So, generate follow-up\
 questions when one or more of the following conditions are met for the candidate's answer:\
\n1. When the candidate's response to the question is unclear or vague.\
\n2. When the candidate's initial answer is too brief, incomplete or lacks details.\
\n3. When you need to probe deeper into the candidate's past behavior and actions in specific situations.\
\n4. When you need to assess the candidate's technical or domain-specific knowledge thoroughly.\
\n5. When you want to explore the candidate's behavior, decision-making processes, problem-solving\
 abilities, and interpersonal skills.\
\n6. When you want to understand how the candidate would approach and resolve hypothetical scenarios.\
\n7. When you want to assess the candidate's ability to adapt to changing circumstances and handle\
 unexpected challenges.\
\n\nAvoid generating follow-up questions when the candidate explicitly states a lack of knowledge on\
 a particular concept and also avoid generating questions when the candidate's response is comprehensive,\
 detailed, and effectively addresses the question, indicating good knowledge on the topic/concept.\
\nFirstly, generate a score measuring the importance of the follow-up\
 question needed in this scenario ranging from 1 to 10. Generate follow-up questions only if the\
 importance score is greater than {importance_score}. If the importance score is lesser than\
 or equal to {importance_score}, do not generate any question.\n\nNow, given a candidate's response\
 to a question or a set of questions in the sequence they were asked, generate\
 follow-up questions, only if much needed, based on the candidate's response. Ensure that the\
 follow-up questions are concise and directly related to the candidate's last answer."

            if number_of_cross_questions == 2:
                template += "Choose number of questions according to the situation, analyzing how many follow-up questions are needed as you are intelligent enough to do that but remember you can generate maximum\
 {number_of_cross_questions} questions. That means you can generate less than or equal to {number_of_cross_questions}\
 questions, i.e. zero, one or two questions if feasible, but not more than {number_of_cross_questions} questions in any case.\n\n"

                extra_format_instruction = '\n\nStrict Instructions: Do not generate more than {number_of_cross_questions} questions in any case. Output should be\
 either zero, one or two questions, where number of questions are decided on the basis of importance score.'
            else:
                template += "Choose number of questions according to the situation, analyzing how many follow-up questions are needed as you are intelligent enough to do that but remember you can generate maximum\
 {number_of_cross_questions} questions. That means you can generate less than or equal to {number_of_cross_questions}\
 questions if feasible, but not more than {number_of_cross_questions} questions in any case.\n\n"

                extra_format_instruction = ''
        else:
            template += "Your primary task is to generate a single, high-quality follow-up question\
 based on the candidate's responses to questions. However, you should do so selectively. So, generate\
 a follow-up question when one or more of the following conditions are met for the candidate's answer:\
\n1. When the candidate's response to the question is unclear or vague.\
\n2. When the candidate's initial answer is too brief, incomplete or lacks details.\
\n3. When you need to probe deeper into the candidate's past behavior and actions in specific situations.\
\n4. When you need to assess the candidate's technical or domain-specific knowledge thoroughly.\
\n5. When you want to explore the candidate's behavior, decision-making processes, problem-solving\
 abilities, and interpersonal skills.\
\n6. When you want to understand how the candidate would approach and resolve hypothetical scenarios.\
\n7. When you want to assess the candidate's ability to adapt to changing circumstances and handle\
 unexpected challenges.\
\n\nAvoid generating follow-up question when the candidate explicitly states a lack of knowledge on\
 a particular concept and also avoid generating question when the candidate's response is\
 comprehensive, detailed, and effectively addresses the question, indicating good knowledge on the\
 topic/concept.\nFirstly, generate a score measuring the importance of the follow-up\
 question needed in this scenario ranging from 1 to 10. Generate follow-up question only if the\
 importance score is greater than {importance_score}. If the importance score is lesser than\
 or equal to {importance_score}, do not generate any question.\n\nNow, given a candidate's response\
 to a question or a set of questions in the sequence they were asked, generate a single follow-up\
 question, only if much needed, based on the candidate's response. Ensure that the follow-up question\
 is concise and directly related to the candidate's last answer.\n\n"

            extra_format_instruction = ' Example 3 (representing 1 question): [\"Can you do overtime?\"].\
\n\nStrict Instructions: Do not generate more than a single/one question in any case. Output should be\
 either zero or one question on the basis of importance score.'
        human_template = "{question_answer}"
        prompt = ChatPromptTemplate.from_messages(
            [SystemMessagePromptTemplate.from_template(template),
             HumanMessagePromptTemplate.from_template(human_template),
             SystemMessagePromptTemplate.from_template('{format_instructions}' + extra_format_instruction)]
        )
        return prompt

    if type == "answer_review_generation":
        template += "You are given a question and the candidate's answer.\
 Your task is to do a detailed analysis of the answer. You need to generate\
 score of the answer in a range of 0 to 10 denoting how good the candidate's answer is, where\
 higher score denotes better answer. You also need to generate a detailed review of the answer\
 highlighting overall quality of the answer including where it was good and where it was bad.\
 You also need to generate all improvements\
 including minute details that need to be done to make candidate's answer better.\
 Also generate a perfect answer of the question.\
 Note that the output will be provided to the candidate, so use direct speech as you are\
 advising the candidate. So, use 'you' to refer to the candidate.\n"

        human_template = "Question: {question}\nCandidate's Answer: {answer}\n\n{format_instructions}"
        prompt = ChatPromptTemplate.from_messages(
            [SystemMessagePromptTemplate.from_template(template),
             HumanMessagePromptTemplate.from_template(human_template)]
        )
        return prompt

    if type == "review_generation":
        template += "You are given all the questions asked during the interview and candidate's answer to it.\
 Your task is to do a detailed analysis of the candidate on the basis of it. Generate a detailed\
 review of the candidate including where he was good and where he was bad. Also, generate score of the candidate ranging\
 from 0 to 10 where higher the score means better the candidate. Also generate, strong and weak\
 points/domains/fields of the candidate in a detailed and formatted manner.\
 You also need to generate all improvements including\
 minute details that can to be done to make the candidate a better fit. Also tell if you will select\
 the candidate or not with the detailed reason of why if selected and why not if not selected.\
 The output will be provided to the candidate, so use direct speech as you are\
 advising the candidate. So, use 'you' to refer to the candidate.\n"
        human_template = "{question_answer}\n{format_instructions}"
        prompt = ChatPromptTemplate.from_messages(
            [SystemMessagePromptTemplate.from_template(template),
             HumanMessagePromptTemplate.from_template(human_template)]
        )
        return prompt


def generate_questions(interview, number_of_questions):
    output_parser = OutputParser()
    format_instructions = output_parser.get_format_instructions()
    prompt = prompt_generator(interview, "question_generation")
    chain = make_question_generation_chain(prompt, output_parser)
    response = None

    retries = 0
    while True:
        if retries > 5:
            print("Maximum retries passed")
            break
        try:
            with get_openai_callback() as cb:
                response = chain({'number_of_questions': number_of_questions,
                                 'format_instructions': format_instructions})
                cost_inr = cb.total_cost*83.06
                print("Cost", cost_inr)
                interview.cost_question_generation += cost_inr
                interview.save()
            break
        except OutputParserMalfunctionException:
            print("Outputparser exception occures")
            retries += 1
            continue
        except Exception as e:
            print(f"Exception occurred during response generation: {e}")
            break

    if response:
        return response['text']
    else:
        # Handle what to show to users
        print("No response generated")


def generate_cross_question(interview, question, number_of_cross_questions, importance_score):
    output_parser = OutputParser()
    format_instructions = output_parser.get_format_instructions()
    prompt = prompt_generator(interview, "cross_question",number_of_cross_questions)
    chain = cross_question_chain(prompt, output_parser)
    response = None
    pos_start = math.floor(question.pos)
    pos_end = pos_start + 1
    questions = models.UserQuestionAnswer.objects.filter(user=interview.user, session=interview,
                                                         is_asked=True, pos__gte=pos_start,
                                                         pos__lt=pos_end)
    question_answer = ""
    for question in questions:
        question_answer += f"Question: {question.question}\nCandidate's Answer: {question.answer}\n\n"
    retries = 0
    while True:
        if retries > 3:
            print("Maximum retries passed")
            break
        try:
            with get_openai_callback() as cb:
                response = chain({'number_of_cross_questions': number_of_cross_questions,
                                  'importance_score': importance_score,
                                  'format_instructions': format_instructions,
                                  'question_answer': question_answer})
                cost_inr = cb.total_cost*83.06
                print("Cost", cost_inr)
                interview.cost_question_generation += cost_inr
                interview.save()
            break
        except OutputParserMalfunctionException:
            print("Outputparser exception occures")
            retries += 1
            continue
        except Exception as e:
            print(f"Exception occurred during response generation: {e}")
            break

    if response:
        return response['text']
    else:
        return []
        # Handle what to show to users
        print("No response generated")


def make_question_generation_chain(prompt, output_parser):
    model = OpenAI(
        model_name="gpt-3.5-turbo-0613",
        temperature=0.6,
        verbose=True
    )
    chain = LLMChain(llm=model, output_parser=output_parser, prompt=prompt, verbose=True)
    return chain


def make_review_generation_chain(prompt, output_parser, model_name):
    model = OpenAI(
        model_name=model_name,
        temperature=0.2,
        verbose=True
    )
    chain = LLMChain(llm=model, prompt=prompt, output_parser=output_parser, verbose=True)
    return chain


def cross_question_chain(prompt, output_parser):
    model = OpenAI(
        model_name="gpt-3.5-turbo-0613",
        temperature=0.2,
        verbose=True
    )
    chain = LLMChain(llm=model, output_parser=output_parser, prompt=prompt, verbose=True)
    return chain


def testing_chain(prompt, output_parser):
    responses = ["Have you worked on Tensorflow?"]
    model = FakeListLLM(responses=responses)
    chain = LLMChain(llm=model, prompt=prompt, output_parser=output_parser, verbose=True)
    return chain


def generate_answer(job_role, question):
    template = "You are an candidate giving an interview for the role of {job_role}. You are neither too good nor too bad. You are an average candidate. Given the question asked by the interviewer, generate an average answer which should neither be good nor bad.\n\n"
    human_template = "Question: {question}\nAverage answer:"
    prompt = ChatPromptTemplate.from_messages(
            [SystemMessagePromptTemplate.from_template(template),
             HumanMessagePromptTemplate.from_template(human_template)]
        )
    model = OpenAI(
        model_name="gpt-3.5-turbo-0613",
        temperature=0.2,
        verbose=True
    )
    chain = LLMChain(llm=model, prompt=prompt, verbose=True)
    response = chain({'job_role': job_role, 'question': question})
    return response['text']
