from migpt import models
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI
from langchain.llms import OpenAI
from langchain.chains import ConversationalRetrievalChain, LLMChain
from langchain.vectorstores import Milvus
from langchain.output_parsers import CommaSeparatedListOutputParser
from langchain.llms.fake import FakeListLLM
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field, validator
from langchain.prompts import (
    SystemMessagePromptTemplate,
    PromptTemplate,
    ChatPromptTemplate,
    HumanMessagePromptTemplate
)


class AnswerReview(BaseModel):
    score: int = Field(description="Score of candidate's answer")
    review: str = Field(description="Review of the answer.")
    improvements: str = Field(description="Improvements in the candidate's answer")
    perfect_answer: str = Field(description="Perfect answer for the question")


class InterviewReview(BaseModel):
    score: int = Field(description="Score of candidate's interview")
    review: str = Field(description="Review of the interview.")
    strong_points: str = Field(description="Strong points, domains of the candidate.")
    weak_points: str = Field(description="Weak points, domains of the candidate.")
    improvements: str = Field(description="Improvements in the candidate.")
    is_selected: bool = Field(description="Will you select the candidate or not?")


def complete_interview(interview_id):
    interview = models.UserInterview.objects.get(id=interview_id)
    interview.is_complete = True
    interview.save()
    userprofile = models.UserProfile.objects.get(user=interview.user)
    userprofile.token -= 1
    userprofile.save()
    # We can charge extra to get answer level review as we'll have to make several api costs
    generate_answer_review(interview)
    generate_review(interview)


def generate_answer_review(interview):
    prompt = prompt_generator(interview, "answer_review_generation")
    output_parser = PydanticOutputParser(pydantic_object=AnswerReview)
    responses = ['{"score": "8", "review": "Good Answer",' +
                 '"improvements": "Improvements are", "perfect_answer":"Perfect answer is"}']
    chain = make_review_generation_chain(prompt, output_parser, responses)
    questions = models.UserQuestionAnswer.objects.filter(user=interview.user, session=interview,
                                                         is_asked=True, answer__isnull=False)
    for question in questions:
        response = chain({'question': question.question,
                          'answer': question.answer,
                          'format_instructions': output_parser.get_format_instructions()})
        question.score = response['text'].score
        question.review = response['text'].review
        question.improvements = response['text'].improvements
        question.perfect_answer = response['text'].perfect_answer
        question.save()


def generate_review(interview):
    prompt = prompt_generator(interview, "review_generation")
    output_parser = PydanticOutputParser(pydantic_object=InterviewReview)
    questions = models.UserQuestionAnswer.objects.filter(user=interview.user, session=interview,
                                                         is_asked=True, answer__isnull=False)
    question_answer = ""
    for question in questions:
        question_answer += f"Question: {question.question}\nAnswer: {question.answer}\n\n"
    responses = ['{"score": "8", "review": "Medium Interview",' +
                 '"strong_points": "Strong Points", "weak_points": "Weak points",' +
                 '"improvements": "Improvements are", "is_selected":"False"}']
    chain = make_review_generation_chain(prompt, output_parser, responses)
    response = chain({'question_answer': question_answer,
                      'format_instructions': output_parser.get_format_instructions()})

    interview.score = response['text'].score
    interview.review = response['text'].review
    interview.strong_points = response['text'].strong_points
    interview.weak_points = response['text'].weak_points
    interview.improvements = response['text'].improvements
    interview.is_selected = response['text'].is_selected
    interview.save()

def feed_data():
    pass


def prompt_generator(interview, type):
    template = "You are an interviewer. "

    if interview.company:
        template += f"You work for {interview.company}. "

    template += f"You are hiring for role of {interview.job_role}. "

    if interview.job_description:
        template += f"The job description is: {interview.job_description}.\n"

    template += f"The round number is {interview.interview_round}. "

    if type == "question_generation":
        
        template += "Generate {number_of_questions} questions regarding it to test if the candidate is a valid fit."

        if interview.subject:
            template += f"You need to access the candidate's skill on {interview.subject}. "

        if interview.topic:
            template += f"Furthermore, you should focus only on {interview.topic}. "

        if interview.tools:
            template += f"You should test candidate's knowledge on following tools: {interview.tools}. "

        if interview.difficulty_level:
            template += f"The difficulty level of questions should be {interview.difficulty_level}. "
        else:
            template += "You should generate questions for every difficulty level, i.e., easy, medium and hard.  "

        if interview.user_instructions:
            template += f"Further instructions are: {interview.user_instructions}."

        template += "Include a variety of questions so both theoretical and practical\
 knowledge of the candidate can be checked. The questions asked should be in a sequence like first ask all questions\
 belonging to the same domain and then jump to the next domain and do the same to judge the candidate\
 topic and domain wise.\n{format_instructions}"

        prompt = PromptTemplate.from_template(template)
        return prompt

    if type == "answer_review_generation":
        template += "You are given question and candidate's answer. You need to generate score of the answer\
 in a range of 1 to 10 denoting how good the user's answer is where higher score denotes better answer. You also need to generate review of the answer highlighting overall quality of the answer and how an interviewer would react to such answer and where it was good and where it was bad. You also need to generate all improvements including minute details that need to be done to make candidate's answer better. Also generate a perfect answer for the question.\n{format_instructions}"

        human_template = "Question: {question}\nAnswer: {answer}"
        prompt = ChatPromptTemplate.from_messages(
            [SystemMessagePromptTemplate.from_template(template),
             HumanMessagePromptTemplate.from_template(human_template)]
        )
        return prompt
    if type == "review_generation":
        template += "You are given all the questions asked and candidate's answer to it. You need to generate review of the interview. Also, generate score of the candidate ranging from 1 to 10 where higher score means better the candidate. Also generate, strong and weak points/domains/fields of the candidate. You also need to generate all improvements including minute details that need to be done to make candidate better. Also tell if you will select the candidate or not.\n{format_instructions}"
        human_template = "{question_answer}"
        prompt = ChatPromptTemplate.from_messages(
            [SystemMessagePromptTemplate.from_template(template),
             HumanMessagePromptTemplate.from_template(human_template)]
        )
        return prompt

def generate_questions(interview):
    prompt = prompt_generator(interview, "question_generation")
    output_parser = CommaSeparatedListOutputParser()
    format_instructions = output_parser.get_format_instructions()
    chain = make_question_generation_chain(prompt, output_parser)
    response = chain({'number_of_questions': "3",
                      'format_instructions': format_instructions})
    return response['text']


def make_question_generation_chain(prompt, output_parser):
    model = OpenAI(
        model_name="gpt-3.5-turbo",
        temperature="0",
    )
    responses = ["Tell me about yourself, Where did you studied, What is DSA?,"]
    llm = FakeListLLM(responses=responses)
    chain = LLMChain(llm=llm, prompt=prompt, output_parser=output_parser, verbose=True)
    return chain


def make_review_generation_chain(prompt, output_parser, responses):
    llm = FakeListLLM(responses=responses)
    chain = LLMChain(llm=llm, prompt=prompt, output_parser=output_parser, verbose=True)
    return chain


def make_chain(prompt):
    model = ChatOpenAI(
        model_name="gpt-3.5-turbo",
        temperature="0",
    )

    vector_db = Chroma(
        collection_name="interview-data",
        embedding_function=OpenAIEmbeddings(),
    )

    chain = ConversationalRetrievalChain.from_llm(
        model,
        retriever=vector_db.as_retriever(),
        return_source_documents=False,
        verbose=True,
        combine_docs_chain_kwargs=dict(prompt=prompt),
        rephrase_question=False,
        return_generated_question=False,
    )
    return chain
