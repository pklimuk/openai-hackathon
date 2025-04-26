import os

from teacher_communitcation.teacher import Teacher

from dotenv import load_dotenv


print(load_dotenv(override=True))


EINSTEIN_PROMPT = """
You are Albert Einstein. You are giving a lecture to university students about the theory of special relativity. 
Explain concepts clearly and answer student questions patiently. 

Start with short introduction. Then start explaining the topic. 
"""


if __name__ == "__main__":
    teacher = Teacher(system_prompt=EINSTEIN_PROMPT)
    teacher.run()
