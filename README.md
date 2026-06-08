# The Unofficial Guide — Project 1

> **How to use this template:**
> Complete each section *after* you've built and tested the corresponding part of your system.
> Do not write placeholder text — if a section isn't done yet, leave it blank and come back.
> Every section below is required for submission. One-liners will not receive full credit.

---

## Domain

<!-- What topic or category of knowledge does your system cover?
     Why is this knowledge valuable, and why is it hard to find through official channels?
     Example: "Student reviews of CS professors at [university] — useful because official
     course descriptions don't reflect teaching style, exam difficulty, or workload." -->

This system covers student-generated knowledge about Computer Science professors and courses at the University of New Orleans. It pulls together Rate My Professor reviews for eight UNO CS instructors plus two Reddit threads, one on the CS program generally, one comparing UNO to Loyola to answer questions about teaching style, exam difficulty, workload, and what taking these classes is actually like.

None of this lives in official channels. The course catalog tells you a class is three credits and lists its prerequisites; it won't tell you that one professor's exams are harder than the material lets on, or that another is genuinely understanding when something comes up mid-semester. That only comes from students who sat through the course, and it's currently spread across review sites and years-old forum posts that nobody wants to dig through. This system collects it in one place and lets you ask it directly.

---

## Document Sources

<!-- List every source you collected documents from.
     Be specific: include URLs, subreddit names, forum thread titles, or file names.
     Aim for variety — sources that together cover different subtopics or perspectives. -->

| # | Document |Source | Description | URL or location |  
|---|--------|--------|-------------|-----------------| 
| 1 |christopher_summa.txt |Rate My Professor |Student reviews | data/raw/christopher_summa.txt
| 2 |vassil_rousser.txt  | Rate My Professor| Student reviews| data/raw/vassil_rousser.txt
| 3 |tamjidul_hoque.txt  |Rate My Professor | Student reviews| data/raw/tamjidul_hoque.txt
| 4 |ted_holmberg.txt  |Rate My Professor | Student reviews| data/raw/ted_holmberg.txt
| 5 |james_wagner.txt |Rate My Professor |Student reviews | data/raw/james_wagner.txt
| 6 |manuel_zumbieta.txt  | Rate My Professor| Student reviews| data/raw/manuel_zumbieta.txt
| 7 |abdullah_nur.txt  |Rate My Professor |Student reviews | data/raw/abdullah_nur.txt
| 8 | abdullah_newaz.txt|Rate My Professor | Student reviews|data/raw/abdullah_newaz.txt
| 9 |reddit_cs_at_uno.txt |Reddit (r/UNO) |student discussion about the UNO computer science program | https://www.reddit.com/r/UNO/comments/1o5uoo/cs_at_uno/
| 10 | reddit_uno_vs_loyola_cs.txt|Reddit (r/NewOrleans) |Student discussion comparing the computer science program at UNO and Loyola|https://www.reddit.com/r/NewOrleans/comments/a4qvpi/uno_vs_loyola_computer_science/
---

## Chunking Strategy

<!-- Describe your chunking approach with enough specificity that someone else could reproduce it.
     Include:
     - Chunk size (characters or tokens) and why that size fits your documents
     - Overlap size and why (or why not) you used overlap
     - Any preprocessing you did before chunking (e.g., stripping HTML, removing headers)
     - What your final chunk count was across all documents -->

**Chunk size:** 800

**Overlap:** 150

**Why these choices fit your documents:**
used an 800-character chunk size because each review includes metadata such as professor name, course, rating, difficulty, and the review text. This size keeps most individual reviews together while still remaining focused for retrieval. I used a 150-character overlap so that if a longer review is split, important context near the boundary is preserved in both chunks.

**Final chunk count:**
Total chunks created: 66
---

## Embedding Model

<!-- Name the embedding model you used and explain your choice.
     Then answer: if you were deploying this system for real users and cost wasn't a constraint,
     what tradeoffs would you weigh in choosing a different model?
     Consider: context length limits, multilingual support, accuracy on domain-specific text,
     latency, and local vs. API-hosted. -->

**Model used:**
I used all-MiniLM-L6-v2 from the sentence-transformers library. It runs locally, so there's no API key and no per-query cost, and it turns each chunk into a 384-dimensional vector. I picked it because my documents are short student reviews, not long technical writeups, and it's fast enough that re-embedding the whole corpus takes a couple of seconds on my laptop. The vectors go into ChromaDB with cosine distance, which is what makes the relevance threshold in query.py actually mean something. For a dataset this small, a heavier model would have been overkill.

**Production tradeoff reflection:**
If real students were depending on this, a few things would worry me. MiniLM only reads about 256 tokens, so a long review gets cut off before it's even embedded, and I'd want a model with a longer window so I'm not silently throwing away the second half of someone's review. A bigger embedding model from OpenAI or Voyage would probably handle the slangy, sarcastic way students actually write better, since MiniLM tends to whiff on nicknames and inside jokes. But those are API-hosted. Every query would leave my machine, add network latency, and ship student opinions off to a third party. So accuracy isn't the only thing on the scale here. I'd be trading privacy and speed for a retrieval bump, and for a review corpus this small I'm not convinced that trade is worth making.

---

## Grounded Generation

<!-- Explain how your system enforces grounding — how does it prevent the LLM from answering
     beyond the retrieved documents?
     Describe both your system prompt (what instruction you gave the model) and any structural
     choices (e.g., how you formatted the context, whether you filtered low-relevance chunks).
     Do not just say "I told it to use the documents" — show the actual instruction or explain
     the mechanism. -->

**System prompt grounding instruction:**
Grounding happens in two places. There's a short system message ("You answer only from retrieved context and cite sources."), and then a longer rules block in the user prompt that spells it out: answer using ONLY the provided context, don't use outside knowledge, and if none of the context is related, reply with the exact line "I don't have enough information in the provided documents to answer that." I also run the model at temperature 0.2 so it stays close to the source text.

The prompt isn't the only guardrail, though. Before the context is even built, I filter the retrieved chunks by cosine distance and drop anything above 0.85, since those are too weakly related to be useful. If nothing survives that filter, the code returns the "not enough info" line directly and never calls the LLM. So an off-topic question can't produce a hallucinated answer, because the model never sees a prompt to answer.

**How source attribution is surfaced in the response:**
Each chunk enters the context with a labeled header like [Source 1: Vassil Roussev (uno_cs_reviews.txt)], so the model can see which professor and file a passage came from and cite it inline. I also return a separate deduplicated list of source filenames next to the answer, so the user still gets attribution even if the model forgets to cite something in its prose.

---

## Evaluation Report

<!-- Run your 5 test questions from planning.md through your system and record the results.
     Be honest — a partially accurate or inaccurate result that you explain well is more
     valuable than a suspiciously perfect result. -->

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 |What do students say about Christopher Summa's teaching style? |Student reviews describe Christopher Summa as a knowledgeable and organized instructor who explains concepts clearly. While many students praise his teaching, some mention that he relies heavily on PowerPoint slides and may not be as supportive for students who struggle |Students have mixed opinions about Christopher Summa's teaching style. Many appreciate his clear explanations, while some criticize his tendency to read from PowerPoint slides, which may not benefit all learners. There are also comments about him seeming rude or burnt out. Overall, he is viewed positively, particularly by those who can engage with his lectures. |Relevant |Accurate|
| 2 | What advice do students give for succeeding in the UNO Computer Science program? | Students recommend completing all assignments, staying consistent with coursework, and building a strong understanding of Computer Science concepts to succeed in the program. |Students recommend completing all assignments in the UNO Computer Science program, particularly in the CSCI 2125 course, to optimize performance in midterms and finals. The program is recognized as one of the best in the state, offering a robust curriculum that deepens understanding of Computer Science concepts. |Relevant |Partially accurate |
| 3 | What do students say about UNO's cybersecurity and internship opportunities? |The answer should mention areas such as cybersecurity/information assurance, internship opportunities, industry connections, or curriculum quality, citing the Reddit documents. |Students recognize the Computer Science program at UNO for its robust cybersecurity curriculum, numerous internship prospects, strong connections within the industry, and specialized courses, including reverse engineering. |Relevant | Accurate |
| 4 |According to student reviews, what factors make a Computer Science course difficult? |The answer should summarize common themes such as heavy programming projects, challenging exams, workload, or independent learning requirements, using information from multiple professor review documents. |Student reviews indicate that challenges in Computer Science courses stem from the difficulty of the material, the challenging exams, and the importance of passing as these courses serve as prerequisites for many other C.S. classes.|Relevant |Partially accurate |
| 5 |According to the collected discussions, why might a student choose UNO over Loyola for Computer Science? |The answer should mention factors such as the established CS program, cybersecurity specialization, industry connections, internship opportunities, lower cost, or program reputation |Students may prefer UNO over Loyola for Computer Science due to its established program, connections to local companies, and specialized routes in bioinformatics and cybersecurity. Additionally, UNO is viewed as more affordable compared to the more expensive Loyola. |Relevant |Accurate|

**Retrieval quality:** Relevant / Partially relevant / Off-target  
**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

<!-- Identify at least one question where retrieval or generation did not work as expected.
     Write a specific explanation of *why* it failed, tied to a part of the pipeline.

     "The answer was wrong" is not an explanation.

     "The relevant information was split across a chunk boundary, so retrieval returned
     only half the context — the model didn't have enough to answer correctly" is an explanation.

     "The embedding model treated the professor's nickname as out-of-vocabulary and returned
     results from an unrelated review" is an explanation. -->

**Question that failed:**
According to student reviews, what factors make a Computer Science course difficult?"

**What the system returned:**
According to student reviews, factors that make a Computer Science course difficult include the material being hard (Source 3: christopher_summa.txt) and the exams being challenging (Source 3: christopher_summa.txt). Additionally, the course being a prerequisite for most C.S classes and requiring a pass to progress can add to the difficulty (Source 3: christopher_summa.txt). However, some courses may be considered easy but unclear or confusing, which can also contribute to difficulty (Source 4: abdullah_newaz.txt).

**Root cause (tied to a specific pipeline stage):**
This breaks at the embedding and retrieval stage. Every review chunk starts with the same boilerplate - Professor: …, Review:, Course: CSCI … — so when I embed the question, the model latches onto that shared structure and the course names instead of the idea of difficulty. The thing that actually says how hard a course is, the Difficulty: 2.0 rating, is just a number sitting in the text, and the embedding model has no real sense of what a 2 versus a 4 means. So I asked for hard courses and got back three easy ones (difficulty 2–3, one of them literally saying "easy") with only a single chunk on target. It got worse from there: two of the four results were near-duplicate reviews of the same professor, so half of my TOP_K=4 budget went to redundant text and the model never saw a wide enough sample to find a real theme.

**What you would change to fix it:**
I'd start by stripping the rating lines out of the embedded text and keeping them as metadata, so the vector reflects what students actually wrote rather than fields every review shares. Then I'd raise TOP_K and dedupe by professor before building the context, so one person's reviews can't take over half the results. If I wanted to go further, I could pre-filter on the numeric difficulty rating — pull reviews rated 4 or 5 first — and let the embedding rank within that set. That way the structured score does the filtering it's suited for, instead of asking the model to infer difficulty from text that never mentions it.

---

## Spec Reflection

<!-- Reflect on how planning.md shaped your implementation.
     Answer both questions with at least 2–3 sentences each. -->

**One way the spec helped you during implementation:**
Writing down the concrete numbers before any code existed meant I wasn't guessing later. The spec already committed to all-MiniLM-L6-v2, a top-k of 4, and an 800/150 chunk size, so when I built retrieve.py and ingest.py I was filling in values I'd already reasoned through instead of second-guessing them mid-build. The five evaluation questions helped too, I pasted them straight into the test block at the bottom of retrieve.py, so the spec gave me my first round of test queries for free.

**One way your implementation diverged from the spec, and why:**
The spec described plain fixed-size chunking: 800 characters with 150 overlap. Once I looked at the actual files, that didn't fit, each Rate My Professor file is a stack of separate reviews, and a blind character split would cut one review off mid-sentence and glue the tail of one professor's review onto the start of another's. So I rewrote chunk_text() to split on the "review N:" markers and make one chunk per review, keeping the 800/150 character split only as a fallback for the rare review that runs long. I also pulled the header boilerplate (department, course list, URL) out of the embedded text and into metadata, which the spec never mentioned, since that block is identical across every chunk and just adds noise to the embedding.

---

## AI Usage

<!-- Describe at least 2 specific instances where you used an AI tool during this project.
     For each: what did you give the AI as input, what did it produce, and what did you
     change, override, or direct differently?

     "I used Claude to help me code" is not sufficient.
     "I gave Claude my Chunking Strategy section from planning.md and asked it to implement
     chunk_text(). It returned a function using a fixed character split. I overrode the
     chunk size from 500 to 200 because my documents are short reviews, not long guides." -->

**Instance 1 — ChatGPT (writing pipeline code)**

- What I gave the AI: My Retrieval Approach section from planning.md (all-MiniLM-L6-v2, top-k 4), and asked it to write ```build_vector_store()``` and ```retrieve()``` with ChromaDB.
- What it produced: Functions that embedded the chunks and ran queries fine, but it left ChromaDB on its default distance metric, squared L2.
- What I changed or overrode: Those L2 distances came back high — around 0.9 to 1.4 — even for good matches, which quietly broke the relevance threshold I wanted to add later. I switched the collection to cosine distance so the scores were comparable across documents, then added a ```MAX_DISTANCE``` cutoff in ```query.py``` that drops weak chunks before the model ever sees them.

**Instance 2 - Claude (debugging retrieval and reflection)**

- What I gave the AI: My three source files and one of my evaluation questions, and asked it to walk through how that question actually moves through the pipeline.
- What it produced: It ran the retrieval for me and showed that when I ask what makes a CS course difficult, three of the four chunks that come back are about easy courses — the embedding was keying on the shared header text, not on difficulty.
- What I changed or overrode: That became my Failure Case section, but I rewrote the explanation myself, and I only kept one of the fixes it floated (stripping the rating lines out of the embedded text) since the others felt like more work than they were worth for a corpus this small.
