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


def make_chain():
    model = ChatOpenAI(
        model_name="gpt-3.5-turbo",
        temperature="0",
    )

    system_template = """You are an interviewer. You are conducting an interview for role of {job_role}
 for company {company_name}. Generate {number_of_questions} questions regarding it to test if the
 candidate is a valid fit. {question_generation_instructions} Use the following questions asked in
 the past to generate new questions.\n_______________\n{context}"""

    prompt = SystemMessagePromptTemplate(
            prompt=PromptTemplate(
                input_variables=[],
                template=system_template, template_format='f-string', validate_template=True
            ), additional_kwargs={}
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