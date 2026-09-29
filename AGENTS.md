# Project Guidelines

## Skill-First Execution Protocol

Before executing ANY user request or coding task, you MUST adhere to the following workflow:

1. **Analyze Requirements First**: Carefully analyze the scope, domain, constraints, and technologies involved in the task.
2. **Review & Match Skills**: Cross-reference the task against all available specialized skills (including TDD, testing, frontend design, database setup, performance optimization, architecture review, codebase comprehension, and code simplification).
3. **Activate the Right Skill**: Explicitly consult and load the matching skill's `SKILL.md` (along with its procedures, checklists, and references) before modifying code or performing operations.
4. **Execute According to Skill Runbooks**: Follow the structured steps, best practices, and verification procedures prescribed by the selected skill to ensure production-grade quality.

## Browser & Testing Rules

1. **Visible Browser Window Only (No Headless)**:
   - Never run or test web applications in headless mode when testing for the user.
   - Always launch a visible, interactive browser window (e.g. via GUI or `cmd.exe /c start <url>`) so the user can see the UI and test results in real-time.

2. **Report Bugs Only (Do Not Auto-Fix During Testing)**:
   - When testing an application or running QA audits, if any bug, error, or defect is discovered, DO NOT fix it automatically.
   - Thoroughly document and report the bug, including error messages, affected components, and behavior observed, allowing the user to decide next steps.
