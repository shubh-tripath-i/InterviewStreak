from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.vectorstores import Milvus
from langchain.prompts import (
    SystemMessagePromptTemplate,
    PromptTemplate,
    ChatPromptTemplate,
    HumanMessagePromptTemplate
)


def feed_data():
    pass


def prompt_generator(interview):
    # Will generate prompt based on given user input

    # template = "You are an interviewer. "

    # if interview.company:
    #     template += "You work for {company}. "

    # template += "You are hiring for role of {job_role}. "

    # if interview.job_description:
    #     template+="The job description is: {job_description}. "

    # if interview.interview_round:
    #     pass

    # if interview.subject:
    #     template+="You need to access the candidate's skill on {subject}. "

    # if interview.topic:
    #     template+="Furthermore, you should focus only on {topic}. "

    # if interview.tools:
    #     template+="You should test candidate's knowledge on following tools: {tools}"

    # template += "The difficulty level of questions should be {difficulty_level}. "

    # if interview.user_instructions:
    #     template+="Further instructions are: {user_instructions}."

#     template += "Include a variety of questions so they can check both theoretical and practical\
#  knowledge of the candidate. The questions asked should be in a sequence like ask all questions\
#  belonging to the same domain and then jump to the next domain and do the same to judge the candidate\
#  topic and domain wise. The following are the questions and answers asked in past. You can\
#  either use the same questions or modify them to generate new questions.\
#  Also, give the answers with it."
#     template += "\n____________\n{context}"

    template = """You are an interviewer. You are conducting an interview for role of {job_role}.
 Generate {number_of_questions} questions regarding it to test if the candidate is a valid fit.
\n{question_generation_instructions}\n The following are the questions and
 answers asked in past. You can either use the same questions or modify them to generate new questions.
 Also, give the answers with it.\n_______________\n{context}"""

    prompt = SystemMessagePromptTemplate(
            prompt=PromptTemplate(
                input_variables=['job_role', 'number_of_questions', 'question_generation_instructions', 'context'],
                template=template, template_format='f-string', validate_template=True
            ), additional_kwargs={}
        )
    return prompt


def generate_questions(interview):
    return ["Tell me about yourself", "What is DSA?"]
    prompt = prompt_generator(interview)
    chain = make_chain(prompt)
    question_generation_instructions = ""
    response = chain({'job_role': "Software Developer",
                      'number_of_questions': "10",
                      'question_generation_instructions': question_generation_instructions })
    print(response)


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
