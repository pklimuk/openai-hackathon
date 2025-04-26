
from teacher_communitcation.presentation import PresentationGenerator



if __name__ == "__main__":
    topic = "The Theory of Special Relativity"
    generator = PresentationGenerator(topic=topic, num_slides=10)
    presentation = generator.generate_presentation()
    