from paw import Paw
from pydantic import BaseModel
from typing import List


class Post(BaseModel):
    title: str
    summary: str


class ContactInformation(BaseModel):
    linkedin: str
    twitter: str
    github: str


class AuthorInformation(BaseModel):
    first_name: str
    last_name: str
    contact_information: ContactInformation
    posts: List[Post]


if __name__ == "__main__":
    paw = Paw(delay=0.1, ignore_links=False)
    result = paw.extract(
        "https://bpradana.github.io",
        output_format=AuthorInformation,
        max_depth=1,
    )

    print(result.model_dump_json(indent=4))

    """
    {
        "first_name": "Bintang Pradana Erlangga Putra",
        "last_name": "Putra",
        "contact_information": {
            "linkedin": "https://linkedin.com/in/bpradana",
            "twitter": "https://twitter.com/bintang_pradana/",
            "github": "https://github.com/bpradana/"
        },
        "posts": [
            {
                "title": "Zero Downtime Deployment on a Blog That No One Reads",
                "summary": "A guide to implementing Blue-Green Deployment using GitHub Actions"
            },
            {
                "title": "AirPods Pro 2nd Generation: a Review and a Rant",
                "summary": "A review of the AirPods Pro 2nd Generation and a rant about Apple's pricing and features."
            },
            {
                "title": "Deploying this site using GitHub Actions",
                "summary": "(not) A guide to deploying a Hugo site using GitHub Actions"
            }
        ]
    }
    """
