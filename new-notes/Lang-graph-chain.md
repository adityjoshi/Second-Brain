# LangChain vs LangGraph — Interview Preparation

## 1. What is LangChain?

LangChain is a framework for building applications powered by Large Language Models (LLMs). It provides components for interacting with LLMs, managing prompts, retrieving information from documents, connecting external tools, and building AI workflows.

Instead of writing all the integration code yourself, LangChain provides reusable components that help you connect different parts of an AI application.

### How does it work?

Consider building a customer support chatbot that answers questions about company policies.

The workflow might look like this:

1. The user asks a question.
2. Your application prepares a prompt containing the question and relevant context.
3. LangChain sends the prompt to an LLM.
4. The LLM generates a response.
5. Your application returns the response to the user.

LangChain provides abstractions for managing these steps and integrating them with other components.

### Example

Suppose a user asks:

> *"What is the company’s refund policy?"*

You can use LangChain to retrieve relevant information from company documents and pass it to an LLM to generate an answer.

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful customer support assistant."),
    ("human", "{question}")
])

model = ChatOpenAI(model="gpt-4.1-mini")
chain = prompt | model

response = chain.invoke({
    "question": "What is the company's refund policy?"
})

print(response.content)

```

**What is happening here?**

* `ChatPromptTemplate` defines the structure of the prompt.
* `ChatOpenAI` provides the interface to the language model.
* The `|` operator connects the prompt to the model.
* `invoke()` executes the chain with the supplied input.

> This is a simple example of composing components into a workflow. It does not retrieve the actual refund policy from a document; you would need to add a retrieval component for that.

### When would you use LangChain?

LangChain is useful when building applications such as:

* RAG (Retrieval-Augmented Generation) systems.
* AI chatbots.
* Document question-answering systems.
* Applications that call external APIs or tools.
* LLM-powered applications that combine prompts, models, and data sources.

---

## 2. What is LangGraph?

LangGraph is a framework for building stateful, multi-step AI workflows using a graph-based execution model.

It allows you to define a workflow as a collection of nodes connected by edges. Each node performs a task, while the edges determine which task should execute next.

Unlike a simple linear chain, LangGraph supports conditional branching, loops, state management, checkpointing, and workflows that can pause for human input.

### Why do we need LangGraph?

Consider an AI research assistant. It needs to:

1. Understand the user’s question.
2. Search the web for relevant information.
3. Evaluate whether the search results are sufficient.
4. Search again if the results are inadequate.
5. Generate a final answer.

This workflow contains decisions and loops. A simple linear chain is not the most natural way to express this logic. LangGraph lets us explicitly define the workflow and its transitions.

### Core components of LangGraph

#### 1. State

State contains the information shared across the workflow.

```python
state = {
    "question": "What is RAG?",
    "search_results": [],
    "answer": "",
    "confidence": 0.0
}

```

As the workflow progresses, nodes can read and update the state.

#### 2. Nodes

Nodes are functions that perform individual tasks. For example:

* `search`: retrieves information.
* `evaluate`: checks whether the information is sufficient.
* `generate`: produces the final answer.

#### 3. Edges

Edges define the flow of execution between nodes:


$$\text{search} \longrightarrow \text{evaluate} \longrightarrow \text{generate}$$

#### 4. Conditional edges

Conditional edges determine the next node based on the current state or the output of a function:

* If search results are sufficient, proceed to answer generation.
* Otherwise, perform another search.

#### 5. Checkpointing

Checkpointing saves workflow state at particular execution points. If a long-running workflow is interrupted, a properly configured checkpointing system can allow it to resume from a saved state rather than restarting everything. Checkpointing can also support persistent conversation state and human approval workflows.

---

## 3. LangGraph Example

Let’s build a small workflow that checks whether a number is greater than 5. If it is, the workflow returns `"high"`. Otherwise, it returns `"low"`.

```python
from typing import TypedDict
from langgraph.graph import StateGraph, START, END

class State(TypedDict):
    value: int
    result: str

def check_value(state: State):
    if state["value"] > 5:
        return {"result": "high"}
    return {"result": "low"}

builder = StateGraph(State)
builder.add_node("check_value", check_value)
builder.add_edge(START, "check_value")
builder.add_edge("check_value", END)

graph = builder.compile()
result = graph.invoke({"value": 10})
print(result)

```

**Output:**

```json
{
    "value": 10,
    "result": "high"
}

```

### How does this workflow execute?

1. `StateGraph(State)` defines a graph whose state follows the `State` schema.
2. `add_node()` registers the function that processes the state.
3. The first edge connects `START` to `check_value`.
4. The second edge connects `check_value` to `END`.
5. `compile()` prepares the graph for execution.
6. `invoke()` executes the workflow with the initial state.

> This example is deliberately simple. In a real AI application, nodes might call an LLM, retrieve documents, or execute tools.

---

## 4. Difference Between LangChain and LangGraph

The most important distinction is that **LangChain** provides components and abstractions for building LLM applications, whereas **LangGraph** provides a way to orchestrate complex, stateful workflows.

| Feature | LangChain | LangGraph |
| --- | --- | --- |
| **Primary purpose** | Build LLM-powered applications | Orchestrate stateful workflows and agents |
| **Execution model** | Chains and composable components | Graphs consisting of nodes and edges |
| **Workflow structure** | Often linear or component-based | Supports branching, loops, and cycles |
| **State management** | Depends on the components and abstractions used | Explicit shared workflow state |
| **Conditional execution** | Possible through its components | A core graph capability |
| **Checkpointing** | Not its primary defining feature | Supports checkpointing through checkpointers |
| **Human intervention** | Can be implemented | Supports workflows that pause and resume around human input |
| **Best suited for** | RAG pipelines, model integration, prompt composition | Agents, iterative reasoning workflows, multi-step automation |

### A Practical Example

Suppose you are building an AI-powered customer support system.

* **Using LangChain:**
1. Receives a question.
2. Retrieves relevant documents.
3. Passes the retrieved context to an LLM.
4. Generates a response.


* **Using LangGraph:**
1. Classifies the customer’s question.
2. Routes it to the appropriate support agent.
3. Retrieves relevant documents.
4. Evaluates the generated answer.
5. Retries if the answer is insufficient.
6. Requests human approval for sensitive cases.
7. Returns the final answer.



LangGraph is particularly useful when the application needs to make decisions about what to do next.

> **Important:** These frameworks are not mutually exclusive. You can use LangChain components inside LangGraph nodes. You do not need to choose one framework exclusively.

---

## 5. What Is an AI Agent, and How Do These Frameworks Help Build One?

An AI agent is a system that uses an LLM to decide what action to take toward a goal, often by interacting with tools and observing their results.

For example, imagine an agent that answers questions about orders. A user asks: *"Where is my order?"*

The agent might:

1. Understand the request.
2. Decide that it needs order information.
3. Call an order lookup API.
4. Examine the API response.
5. Generate an answer using the retrieved information.

The key distinction is that the agent can choose actions based on the situation instead of following only a fixed sequence.

* **Where does LangChain fit?**
LangChain provides integrations and abstractions for:
* LLMs
* Prompts
* Tools
* Data retrieval
* Structured outputs
*(These components help build the individual capabilities of an agent.)*


* **Where does LangGraph fit?**
LangGraph manages the agent’s execution flow, including:
* Which node executes next
* How state is maintained
* How tool results are incorporated
* When the agent should retry or finish
* When execution should pause for human approval



> **Rule of thumb:** LangChain helps you build the components; LangGraph helps you control how those components work together in a complex workflow. Both offer overlapping capabilities.

---

## 6. What Is the Difference Between a Chain and a Graph?

### Chain

A chain generally represents a linear sequence of operations:

$$\text{User Input} \longrightarrow \text{Prompt} \longrightarrow \text{LLM} \longrightarrow \text{Output}$$

Each step feeds into the next. Chains are useful when the workflow is straightforward and does not require complex control flow.

### Graph

A graph represents operations as nodes connected by edges:

```text
          START
            |
            v
          Search
            |
            v
          Evaluate
          /      \
    Sufficient?   No
        /          \
       v            v
    Generate      Search
       |
       v
      END

```

This illustrates conditional execution and a loop. A graph is useful when the application must make decisions, revisit earlier steps, maintain state, or support complex execution patterns.

---

## 7. What Is State in LangGraph?

State is the data shared between nodes during workflow execution.

Suppose you are building a research agent. Its state might contain:

```json
{
    "question": "Explain database indexing",
    "search_results": [],
    "draft_answer": "",
    "review_feedback": "",
    "final_answer": ""
}

```

1. The `search` node updates `search_results`.
2. The `generation` node uses those results to create `draft_answer`.
3. The `review` node examines the draft and updates `review_feedback`.
4. Finally, the `generation` node can use the feedback to produce `final_answer`.

Each node reads the relevant fields from the shared state and returns updates rather than passing every value as an independent argument.

### Why is state important?

State allows a multi-step workflow to preserve information needed by later steps. It makes it easier to implement:

* Multi-turn conversations
* Iterative generation and review
* Tool execution
* Conditional routing
* Workflow recovery through checkpointing

> **Interview takeaway:** State represents what the workflow currently knows; nodes process or update that information, and edges determine what executes next.

---

## 8. What Is Checkpointing in LangGraph?

Checkpointing is the mechanism used to save workflow state so that it can be recovered later.

Consider a research agent that spends several minutes searching documents, analysing evidence, and generating a report. If the process is interrupted, restarting from the beginning wastes time and repeats expensive operations.

With a properly configured checkpointer, LangGraph can persist snapshots of the workflow state at execution checkpoints. When the workflow is resumed using the persisted thread and configuration, it continues from the saved state.

### Why is checkpointing useful?

* **Recovery:** Resume workflows after interruptions.
* **Conversation persistence:** Retain state across interactions.
* **Human-in-the-loop workflows:** Pause for approval and resume afterwards.
* **Debugging:** Inspect the state at earlier execution points.

### Is checkpointing the same as memory?

**No.** Memory refers broadly to information retained for future use (such as conversation history or user preferences). Checkpointing saves the execution state of a workflow. While checkpointing can support memory by persisting state, they are distinct concepts.

> Checkpointing does not automatically guarantee that external operations execute exactly once. If a workflow calls an external payment API, idempotency and error-handling mechanisms are still required.

---

## 9. What Is Human-in-the-Loop in LangGraph?

Human-in-the-loop means incorporating human review or approval into an otherwise automated workflow.

```text
Customer Request
       |
       v
 Analyse Request
       |
       v
 Check Refund Rules
       |
       v
 Refund Eligible?
       |
       v
 Human Approval (System pauses here)
       |
       v
 Process Refund

```

For sensitive actions, the system pauses before executing. A human reviews the request and approves or rejects it. The workflow then resumes with the decision. LangGraph supports this pattern via interrupts and checkpointing.

### Common applications:

* Financial transactions
* Refund approvals
* Production deployments
* Sending important external communications
* Reviewing AI-generated content before publication

---

## 10. Common Interview Questions

### Q1. Can we use LangGraph without LangChain?

**Yes.** LangGraph can be used independently of LangChain, including with models and tools accessed through other libraries or custom code. You do not have to use LangChain for every model interaction.

### Q2. Can LangChain build agents?

**Yes.** LangChain provides agent-building abstractions and integrations. LangGraph is preferred when you need explicit control over state, execution flow, retries, persistence, or human approval.

### Q3. Is LangGraph only for multi-agent systems?

**No.** LangGraph can orchestrate a single agent, multiple agents, or a deterministic workflow that does not use an agent at all. Its defining feature is graph-based orchestration, not agent count.

### Q4. What is a conditional edge?

A conditional edge determines the next node based on a routing function:

```python
def router(state):
    if state["confidence"] > 0.8:
        return "final"
    return "reviewer"

```

The graph routes execution to `final` when confidence is high or `reviewer` otherwise. The function itself does not execute the target node; it only determines routing.

### Q5. What is the difference between a node and an edge?

* A **node** performs an operation (e.g., calling an LLM or retrieving documents).
* An **edge** defines the transition between operations (e.g., routing from search to generate).

### Q6. Why would you choose LangGraph over a simple chain?

Choose LangGraph when the workflow requires conditional routing, loops, shared state, checkpointing, or human intervention. For straightforward prompt-and-response pipelines, a simple chain is simpler to build and maintain.

---

## 11. The Final Interview Answer

If an interviewer asks: *"Explain LangChain and LangGraph, and what is the difference between them?"*, summarize with:

> "LangChain and LangGraph are frameworks for building LLM-powered applications, but they solve different problems.
> **LangChain** provides reusable components for integrating models, prompts, tools, and data sources (such as a standard RAG pipeline).
> **LangGraph** orchestrates complex, stateful workflows using nodes, edges, and shared state, enabling conditional routing, loops, checkpointing, and human-in-the-loop steps.
> In practice, they complement each other: you can use LangChain components inside LangGraph nodes."

**One-line summary to remember:**

* **LangChain** provides the building blocks.
* **LangGraph** provides explicit control over stateful workflows and agent execution.
