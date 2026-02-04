# Customer support agent demo

I want to build a simple demo agent that will act as a customer support agent.

Use some framework like langchain or langgraph or something else (think about which framework to use and conduct some research based on the requirements and tell me why you chose a particular framework )

For the simulation of emails, create a simple web UI where can “send email” with input fields for subject, from email ID, and body and a simple view of the response “email” from the agent.

We can create a simulation of user and order database. Take a very simple approach, some local DB or file system. Think through which approach to take and tell me why you selected that.

The tools can be simple functions that interact with the “database” or the “email app” 

I have n

Use Context7 MCP for fetching any documentation for libraries you use like langchain/langgraph.

Ask me for any clarifications you need on the requirements.

## Example scenario

- Ecommerce company
- Wants to automate order status related queries
- Goal is to reduce cost since order status is purely data fetch and respond
- For this task focus on email queries only

## Solution requirements

- Needs to be auto triggered when emails come
- Needs to have some logic to ensure only order status queries are responded to
- Needs to fetch user and order details
- Need to check email ID is valid user
- Need to respond with order details and status, route to real agents for other queries
- Needs to be aware of org context
- Guard rails
    - Tone needs to be professional but also vary based on customer’s perceived emotion
    - Brand and legal guidelines
    - Prompt injection handling
    - Tool validations (for user ID, order Id its)
- Error handling
    - in case of failures send some default response and route to human queue
- Does not need to be real time response

Out of scope

- Needs to handle replies from user ?? (out of scope)
- having past context of queries already raised by user

## Agent design

### UI

- Not required

### Trigger

- When email is received in some support mail box

### Orchestration layer

System prompt

- Role
- Context - talk about company, what job it will perform, structure of content that will follow (task inputs)
- Task steps
    - fetch user ID from email (if not found send default response)
    - fetch order details for user for last 2 weeks
    - Match order details with email body to find the relevant order (can be order ID or product information)
    - Prepare an Answer the query for the user
    - Send an email response
- Task inputs
    - Email contents (sender, subject, body, attachments)
- Examples
- Guard rails and guidelines
    - If the query is not clear or you are not able to answer it with the steps mentioned, pass the case to human queue

### Tools

- Tool to check user ID from email
- Tool to fetch orders within a date for the
- Tool to send email
- Tool to trigger default responses (different response types)
- Tool to pass the case to human queue

### Knowledge

- Might need in the future when agent starts handling more use cases
- For simple order status query response

### Memory

- N/A since there is no long term context the agent needs to maintain
- Every email can be started fresh

## Guardrails

### Input validation

Use a small cheap model to validate inputs for guardrails

- Right query type (order status) - if not move to human agent queue
- Check for any out of scope queries that are not relevant to ecommerce support agent context
- Prompt injection attack attempts - send default response that you can’t help with that

### Tools validation

Validate input structure and input values. This will be code based validation

- user ID fetch - email should be same as mail sender
- order details fetch, user ID should be same as value from user ID fetch
- send email - email should match sender email

### Output validation

Use a small cheap model to validate outputs for guardrails

- Tone should be professional
- Data points mentioned should match tool responses
- Other legal and compliance stuff (don’t promise stuff that is not true, don’t mention competitor names)