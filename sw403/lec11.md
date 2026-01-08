Here is a comprehensive Mermaid workflow diagram that summarizes the entire lecture. It visualizes the flow from the user request, through the specific Agent roles, the feedback loops, safety mechanisms (checkpoints/retries), and the memory systems.

```mermaid
graph TD
    %% --- Styling ---
    classDef human fill:#f9f,stroke:#333,stroke-width:2px,color:black;
    classDef agent fill:#e1f5fe,stroke:#01579b,stroke-width:2px,color:black;
    classDef tool fill:#fff3e0,stroke:#e65100,stroke-width:1px,color:black;
    classDef memory fill:#e8f5e9,stroke:#1b5e20,stroke-width:1px,stroke-dasharray: 5 5,color:black;
    classDef safety fill:#ffebee,stroke:#b71c1c,stroke-width:2px,color:black;

    %% --- External Actors ---
    User((User Input)):::human
    HumanDev(Human Intervention):::human

    %% --- Memory Systems (Slide 9) ---
    subgraph Memory_System ["🧠 Shared Memory & Context"]
        STM[("Short-Term Memory<br/>(Current Task/Logs)")]:::memory
        LTM[("Long-Term Memory<br/>(Vector DB/Docs/Repo)")]:::memory
    end

    %% --- The Multi-Agent Workflow ---
    subgraph Orchestration ["⚙️ Multi-Agent Orchestration Loop"]
        
        %% Initialization
        Start([Start Workflow]):::tool
        GitSave[("💾 Safety Checkpoint<br/>(Git Commit)")]:::safety

        %% Roles (Slides 10-16)
        Planner(<b>Planner Agent</b><br/>Role: Architect<br/>Tool: Requirements Analyzer):::agent
        Coder(<b>Coder Agent</b><br/>Role: Builder<br/>Tool: Git/Compiler):::agent
        Tester(<b>Tester Agent</b><br/>Role: QA<br/>Tool: Pytest/Mutation Testing):::agent
        Reviewer(<b>Reviewer Agent</b><br/>Role: Senior Eng<br/>Tool: Linter/Security Scan):::agent

        %% Logic Flow
        User --> Start
        Start --> GitSave
        GitSave --> Planner
        
        %% Planning Phase
        Planner -- "JSON Spec + Acceptance Criteria" --> Coder
        
        %% Coding Phase
        Coder -- "Code Patch/Diff" --> Tester
        
        %% Testing Phase (Verification)
        Tester -- "Pass/Fail Metrics" --> DecisionTest{Tests Passed?}
        
        %% The Correction Loop (Slide 18 & 21)
        DecisionTest -- "❌ No (Fail)" --> MetricsCheck{Check Metrics}
        
        %% Safety Mechanisms (Slides 21-23)
        MetricsCheck -- "Retry Limit Not Reached<br/>& Error Decreasing" --> Coder
        MetricsCheck -- "⚠️ Limit Reached OR<br/>Errors Increasing" --> Rollback[("↩️ ROLLBACK<br/>(Git Reset)")]:::safety
        
        %% Review Phase
        DecisionTest -- "✅ Yes (Pass)" --> Reviewer
        Reviewer -- "Quality/Security Issues" --> Coder
        Reviewer -- "✅ Approved" --> Merge([Merge Code / Done]):::tool
        
        %% Fail State
        Rollback --> HumanDev
    end

    %% --- Connections to Memory ---
    Planner <--> LTM
    Coder <--> STM
    Tester -.-> STM
    
    %% --- Theory Annotation (Slide 44) ---
    TheoryNode><i>Theory of Mind (ToM):<br/>Agents anticipate what<br/>other agents need</i>]
    TheoryNode -.-> Planner
    TheoryNode -.-> Reviewer

```

### **How to Read This Diagram**

1.  **The Inputs (Pink):** The process starts with a **User** request (e.g., "Add a search bar") and ends with either a **Merge** or a request for **Human Intervention**.
2.  **The Agents (Blue):**
    *   **Planner:** Converts the vague user request into a strict **JSON Spec** (Slide 11-12).
    *   **Coder:** Takes the spec and writes a **Git Patch** (Slide 13).
    *   **Tester:** The "Ground Truth." It runs tests. If they fail, it sends the specific error logs back to the Coder (Slide 14-15).
    *   **Reviewer:** Checks for maintainability and security *after* the tests pass (Slide 16).
3.  **The Safety Valves (Red):**
    *   **Git Checkpoint:** Before any code changes, the state is saved.
    *   **Rollback & Metrics:** If the Coder gets stuck in a loop or makes the code worse (errors increase), the system stops, rolls back the code (Slide 20), and calls a human. This prevents "Failure Cascades."
4.  **Memory (Green):** Agents pull context from **Long-Term Memory** (API docs) and store progress in **Short-Term Memory** (current errors).