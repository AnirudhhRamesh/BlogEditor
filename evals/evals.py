from math import exp
from time import sleep
from typing import List
from collections import defaultdict
from schemas.file import File
from llms.llm_service import LLMService
import numpy as np
from prompts.prompts import Prompts
# from sentence_transformers import SentenceTransformers



class Evals:
    """
    Evals class for the file object
    """
    def __init__(self, file_helper, llm_service, dataset):
        self.file_helper = file_helper
        self.llm_service = llm_service
        self.prompts = Prompts(self.file_helper)
        self.dataset = dataset

    def _get_attribute(self, file: File, attr: str):
        """
        Get the attribute from the file
        """
        if attr in ["title", "description", "content", "linkedin"]:
            return getattr(file.blog, attr)
        elif attr in ["top_companies", "top_universities"]:
            return getattr(file.metadata.guest, attr)

    def eval_model(self, model: str, attr: str, iterations = 1):
        """
        Evaluate a provided model + prompt configuration for a given attribute against the dataset
        """
        # Run all evals
        evals = []
        for i in range(iterations):
            for file in self.dataset:
                candidate = self.llm_service.prompt(model=model, prompt=self.prompts.get_prompt(file, attr).text)
                reference = self._get_attribute(file, attr)
                evals.append(self.eval_all(candidate, reference, file))

                print(f"candidate: {candidate} \nreference: {reference} \nevals: {evals[-1]}")
                print(f"================================================ \n \n")

                if i > 0:
                    sleep(1)

        # Average the results across iterations
        results = defaultdict(lambda: 0)
        for scores in evals:
            for key, value in scores.items():
                results[key] += value

        for key, value in results.items():
            results[key] /= (iterations * len(self.dataset))

        return results

    def eval_all(self, candidate: str, reference: str, file: File=None):
        """
        Evaluate a generated text agaisnt the entire dataset
        """

        scores = {
            "bleu1": self.bleu_score(candidate, reference, 1),
            "bleu2": self.bleu_score(candidate, reference, 2),
            "bleu3": self.bleu_score(candidate, reference, 3),
            "transcript_overlap": self.transcript_overlap_score(candidate, file.metadata.transcript.text),
            # "rouge": self.rouge_score(candidate, reference),
            # "cosine": self.cosine_similarity(candidate, reference),
            # "perplexity": self.perplexity(candidate, reference)
        }

        return scores

    def _split_text(self, text: str, n: int):
        """
        Split the text into n-grams
        """
        words = text
        if isinstance(text, str):
            words = text.split() #Bad code, but handles top_companies case (parsed as list)
        return [tuple(words[i:i+n]) for i in range(len(words)-n+1)]

    def bleu_score(self, candidate: str, reference: str, n: int = 1) -> float:
        """
        Calculate the BLEU score for a given candidate and reference text
        """
        if not candidate or not reference:
            return 0.0

        candidate_ngrams = self._split_text(candidate, n)
        reference_ngrams = self._split_text(reference, n)   

        # Count occurrences of each n-gram in both texts
        candidate_counts = defaultdict(lambda: 0)
        reference_counts = defaultdict(lambda: 0)
        
        for ngram in candidate_ngrams:
            candidate_counts[ngram] += 1
            
        for ngram in reference_ngrams:
            reference_counts[ngram] += 1

        # Count matches (clipped by reference counts)
        matches = 0
        for ngram, count in candidate_counts.items():
            matches += min(count, reference_counts[ngram])

        # Apply brevity penalty based on word count
        bp = 1.0

        if isinstance(candidate, str):
            candidate_words = candidate.split()
        else:
            candidate_words = candidate

        if isinstance(reference, str):
            reference_words = reference.split()
        else:
            reference_words = reference
        
        if len(candidate_words) < len(reference_words):
            bp = exp(1 - len(reference_words) / len(candidate_words))

        # Calculate final score
        if len(candidate_ngrams) == 0:
            return 0.0
        return bp * (matches / len(candidate_ngrams))

    def transcript_overlap_score(self, candidate: str, transcript: str):
        """
        Calculate the transcript overlap score between the candidate and reference text
        """
        # For each word in the candidate, check if it appears in the reference
        candidate_words = candidate.split()
        transcript_words = set(transcript.split())

        # Count the number of words that appear in both the candidate and reference
        matches = 0
        for word in candidate_words:
            if word in transcript_words:
                matches += 1

        # Return the ratio of matches to the total number of words in the candidate
        return matches / len(candidate_words)

    def rouge_score(self, candidate: str, reference: str):
        #TODO: Implement ROUGE score
        pass

    def cosine_similarity(self, candidate: str, reference: str):
        # embedding_model = SentenceTransformers('all-MiniLM-L6-v2')  # or another suitable model
        
        # if reference not in self.dataset_embeddings:
        #     #cache dataset embeddings
        #     self.dataset_embeddings[reference] = embedding_model.encode(reference)
        
        # # Get embeddings for both texts
        # candidate_embedding = embedding_model.encode(candidate)
        # reference_embedding = self.dataset_embeddings[reference]
        
        # # Calculate cosine similarity
        # return np.dot(candidate_embedding, reference_embedding) / (
        #     np.linalg.norm(candidate_embedding) * np.linalg.norm(reference_embedding)
        # )
        pass

    def sentence_wise_similarity(self, candidate: str, reference: str):
        # """
        # Calculate sentence-by-sentence similarity scores
        # """
        # # Split into sentences
        # candidate_sentences = sent_tokenize(candidate)
        # reference_sentences = sent_tokenize(reference)
        
        # # Calculate similarities for each sentence pair
        # similarities = []
        # for c_sent in candidate_sentences:
        #     sent_scores = []
        #     for r_sent in reference_sentences:
        #         score = self.cosine_similarity(c_sent, r_sent)
        #         sent_scores.append(score)
        #     similarities.append(max(sent_scores))  # Take best match for each candidate sentence
        
        # # Return average similarity
        # return sum(similarities) / len(similarities) if similarities else 0.0
        pass

    def BERTScore(self, candidate: str, reference: str):
        pass

    def perplexity(self, candidate: str, reference: str):
        pass

    def mauve_score(self, candidate: str, reference: str):
        pass

    def compression_ratio(self, candidate: str, reference: str):
        pass

    def rouge_l_score(self, candidate: str, reference: str):
        # Longest common subsequence
        pass
    
    # Knowledge Triplet Evaluation
    def knowledge_triplet_evaluation(self, candidate: str, reference: str):
        pass
    
    # Custom & Advanced evals
    def overlap_score(self, candidate: str, reference: str):
        """
        Get the vocab overlap between generated content & original transcript
        """
        pass

    def llm_judge(self, file: File): #Specific to the task: Blog, Title, LinkedIn, etc.
        pass

    #Util funcs
    def _embed_file(self, file: File):
        pass