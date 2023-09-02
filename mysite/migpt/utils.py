# from langchain.vectorstores import Chroma
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

    #     system_template = """You are an interviewer. You are conducting an interview for role of {job_role}
    #  for company {company_name}. Generate {number_of_questions} questions regarding it to test if the
    #  candidate is a valid fit. {question_generation_instructions} Use the following questions asked in
    #  the past to generate new questions.\n_______________\n{context}"""

    template = "You are an interviewer. "

    if interview.company:
        template += "You work for {company}. "

    template += "You are hiring for role of {job_role}. "

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

    template += "The difficulty level of questions should be {difficulty_level}. "

    # if interview.user_instructions:
    #     template+="Further instructions are: {user_instructions}."

    template += "Include a variety of questions so they can check both theoretical and practical\
 knowledge of the candidate. The questions asked should be in a sequence like ask all questions\
 belonging to the same domain and then jump to the next domain and do the same to judge the candidate\
 topic and domain wise. The following are the questions and answers asked in past. You can\
 either use the same questions or modify them to generate new questions.\
 Also, give the answers with it."
    template += "\n____________\n{context}"

    prompt = SystemMessagePromptTemplate(
            prompt=PromptTemplate(
                input_variables=[],
                template=template, template_format='f-string', validate_template=True
            ), additional_kwargs={}
        )
    return prompt


def generate_questions(interview):
    # prompt  = prompt_generator(interview)
    # chain = make_chain(prompt)
    demo_questions = ["Tell me about yourself", "What is DSA?"]
    return demo_questions


def make_chain(prompt):
    model = ChatOpenAI(
        model_name="gpt-3.5-turbo",
        temperature="0",
    )

    vector_db = Milvus(
        collection_name="interview-data",
        embedding_function=OpenAIEmbeddings(),
        # connection_args={"host": "127.0.0.1", "port": "19530"},
    )

    chain = ConversationalRetrievalChain.from_llm(
        model,
        retriever=vector_db.as_retriever(),
        return_source_documents=False,
        verbose=False,
        combine_docs_chain_kwargs=dict(prompt=prompt),
        rephrase_question=False,
        return_generated_question=False,
    )
    return chain
