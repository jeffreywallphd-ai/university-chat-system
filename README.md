# university-chat-system
A system to help students find answers on college campuses

================================================================================
# University Chat System
Michigan Technological University | MIS4100 Business Analytics & Information
Systems Project | Fall 2026, as of 10/5/2026


TABLE OF CONTENTS
--------------------------------------------------------------------------------
  1. Project Overview
  2. Problem Statement
  3. Goals and Objectives
  4. Target Market
  5. Scope and Boundaries
  6. Key Features
  7. Technologies Utilized
  8. Major Milestones
  9. Guardrails (Privacy, Security, Accessibility)
 10. Installation Instructions
 11. Team Members and Developers
 12. Supporting Project Documents


## 1. PROJECT OVERVIEW
--------------------------------------------------------------------------------
UCS is a mobile-first campus information assistant for Michigan
Technological University. It gives students (first), and then faculty,
advisors, and staff, a fast and trustworthy way to get answers about their own
institution from any device, at any time of day.

Rather than creating a new university resource, UCS acts as a single
information layer over resources the university already has. Every answer is
drawn from approved Michigan Tech sources and links back to the official page
it came from. When no approved source covers a question, UCS says so and
points the user to a real person instead of guessing.

UCS is designed as a connected portfolio of campus information products,
not a single chatbot. The planned products are:

  - An answer engine (chatbot) over university policy and written resources
  - A faculty/staff directory with office locations and office hours
  - Campus wayfinding (interactive map and building directions)
  - Staff-facing tools for keeping approved sources accurate and current

Portfolio vision statement:

  "A Michigan Tech where anyone can get a quick, properly sourced answer about
  their university from any device, through a connected set of campus
  information products that make what the institution already knows easy to
  reach and easy to trust."


## 2. PROBLEM STATEMENT
--------------------------------------------------------------------------------
Information about the university is fragmented and difficult to find. Details
about courses, policies, events, deadlines, and faculty contacts are spread
across university websites, Banweb, MTU Experience, department pages, and PDF
links. There is no single place to ask a question and receive a reliable,
quick answer.

  - The information exists, but the time cost of locating it is unpredictable
    and spikes during registration, drop deadlines, and graduation planning.
  - Most questions arise outside office hours, when no one is available to
    ask.
  - Students ask staff simple questions that consume time better spent on
    complex cases.
  - Students often fall back on general-purpose AI tools (e.g., ChatGPT),
    which can give incorrect or outdated information about Michigan Tech.

Evidence from early 2026 student survey (33 student responses):

  - 85% of students (28 of 33) rated their likelihood of using UCS a 4 or
    5 out of 5.
  - Requests clustered around academic navigation: finding the degree audit,
    GPA, transcripts, HASS course lists, registration information, graduation
    application steps, and syllabi.
  - Other recurring requests: parking tickets, campus events, directions,
    housing contract and student bill, and help navigating MTU Experience and
    Banweb.
  - A small faculty sample (3 responses, all rated 5 out of 5) asked for
    classroom assignments per semester, alumni information, and help
    organizing and grading coursework.


## 3. GOALS AND OBJECTIVES
--------------------------------------------------------------------------------
Primary goal:
  Give the Michigan Tech community a quick, accurate, properly sourced way to
  answer questions about their institution, accessible anytime and on any
  device.

Objectives:
  1. Deliver correct, source-cited answers to policy and academic questions
     (e.g., withdrawal deadlines, graduation eligibility, academic standing,
     financial aid links) in under a minute, including at 2 a.m.
  2. Help users find a person and then find the room: look up faculty/staff,
     see office location and availability, and get directions to the building.
  3. Reduce the volume of simple, repetitive questions reaching faculty,
     advisors, and front-desk staff so they can focus on complex cases.
  4. Reduce reliance on "tribal knowledge" for first-year and transfer
     students.
  5. Establish a governed inventory of authoritative campus content, where
     every source has a named owner, an approval state, and a freshness date.
  6. Build a feedback loop that surfaces gaps in source content so content
     owners can fix the source rather than the system.
  7. Design a themeable platform so a second university can adopt UCS
     through configuration rather than a rebuild.
  8. Keep development and iteration costs low enough that improvement can be
     continuous.

Upstream strategy alignment:
  UCS supports the Education goal of Michigan Tech's strategic plan by
  improving access to existing resources, and supports the People goal by
  freeing staff from repetitive questions.


## 4. TARGET MARKET
--------------------------------------------------------------------------------
Primary users
  - Current Michigan Tech students. This is the first and most important
    audience. Within it, the most underserved segments are:
      * First-year students, who lack knowledge of where things live
      * Transfer students, who need credit-transfer and navigation help
      * Upper-level students handling degree audits, registration, and
        graduation planning
      * Graduate students

Secondary users
  - Faculty, academic advisors, and front-desk/department staff, both as
    information seekers (e.g., classroom lookups) and as beneficiaries of
    reduced repetitive questions.

Institutional stakeholders (staff-facing tools)
  - IT and department content owners who maintain the approved source
    registry and respond to content-gap reports.

Future market
  - Other mid-size and smaller universities that want a lightweight,
    student-centered, mobile-first alternative to enterprise platforms.
    UCS's themeable design is intended to make this possible.

Not the target market
  - Prospective students and admissions marketing. UCS is intended for
    current students and the current campus community.

Competitive context (summary):
  Existing tools are mostly enterprise platforms sold top-down to
  administrators: TeamDynamix Conversational AI (IT service management),
  Ivy.ai / Ocelot by Gravyty (higher-ed chatbot), and EAB Navigate360
  (admissions and enrollment). General-purpose AI tools (ChatGPT, Microsoft
  Copilot) are also used informally by students. UCS differentiates on:
    - Mobile-first design
    - Student-defined scope
    - Retrieval-based, policy-aware answers bounded to verified sources
    - Planned campus wayfinding (not offered by the competitors reviewed)
    - Low infrastructure cost
    - Per-institution theming


## 5. SCOPE AND BOUNDARIES
--------------------------------------------------------------------------------
In scope
  - Answers sourced from approved university documents, policies, and web
    content
  - Faculty/staff directory and campus wayfinding (planned follow-on products)
  - Escalation to real people (advisors, offices) from anywhere in the app
  - Semester-aware responses (registration period vs. mid-semester vs. finals)
  - Anonymized usage analytics and user feedback tools
  - Staff/admin tools for source management and institutional theming

Out of scope (deliberate boundaries)
  - Not a general-purpose AI assistant; it only provides information about the
    university.
  - Not the final decision-maker on important matters (e.g., course scheduling
    by semester). It is a resource that helps users find the right person to
    consult.
  - Not a system of record; it pulls from existing sources.
  - Not a ticketing tool or IT help-desk integration.
  - No student data is shared or sold.
  - No admissions or marketing use.


## 6. KEY FEATURES
--------------------------------------------------------------------------------
Core (answer engine)
  - Plain-language question answering with source citations and links
  - Policy, handbook, and course information retrieval
  - Advisor escalation logic: for questions like "Can I overload credits?" the
    app gives a general explanation and directs the user to confirm with their
    advisor, with contact information
  - Role-aware answers (incoming freshman, transfer, graduate, faculty, etc.)
  - "Was this helpful?" and "What information was missing?" feedback prompts
  - Notices when information may be out of date
  - Clear disclosure that users are interacting with an AI

Directory and contacts (planned)
  - Global search by name, department, role, or building, with auto-suggest
  - Faculty/staff profiles with office location, office hours, email, phone,
    and courses taught
  - Filters, department directories, and administrative hierarchy views
  - "View office on map" link between directory and map

Wayfinding (planned)
  - Interactive campus map with building search and directions
  - Layers such as academic buildings, residence halls, dining, and parking
  - Accessibility routes (ramps and elevators)
  - Possible indoor floor maps and building entrances

Campus life (planned)
  - Daily events feed (e.g., from Student Scoop or campus calendars)
  - Building hours, printer locations, parking rules, and club information

Staff and admin tools (planned)
  - Source registry with named owner, approval state, and last-verified date
  - Analytics dashboard: most-asked questions, questions the bot struggles
    with, peak usage times, and common user types
  - Admin theming page so IT can apply institutional styling

Mobile experience
  - Mobile-first design with a home screen widget system, thumb-friendly task
    bar, and a familiar chat-style interface
  - Themeable design system (Michigan Tech colors by default, with a universal
    template other universities can customize)


## 7. TECHNOLOGIES UTILIZED
--------------------------------------------------------------------------------
Note: Some items below are confirmed in project documents and some are
options under evaluation. Items marked (evaluating) are not final decisions.

AI and data retrieval
  - Amazon Bedrock (AWS-hosted foundation models) for the AI layer
  - Retrieval-augmented generation (RAG) so answers come only from approved
    sources
  - Semantic search using embeddings and a vector database
  - Self-hosted open-source language model via Ollama (evaluating)
  - Automated evaluation test set for answer accuracy and citation coverage

Cloud infrastructure
  - Amazon Web Services (AWS), pay-as-you-go model
  - Amazon EC2 (compute) and Amazon EBS (storage)
  - Estimated development-phase cost of roughly $2.50 to $3.00 per month

Data and storage
  - Document database such as MongoDB (evaluating)
  - Source registry (approved sources, owners, approval states, freshness
    dates)
  - Web scraping/crawling of university web content (evaluating)
  - Possible use of data from university (Tech) servers (evaluating)

University system integrations (planned)
  - Banner / Banweb student information system API
  - MTU Experience
  - Faculty/staff directory data
  - Campus calendar and Student Scoop events
  - Student class information system, such as MTU Grades (evaluating)
  - Single sign-on (SSO) and role-based access control for staff tools

Front end and design
  - Mobile application (mobile-first design) with a reusable app shell
  - Themeable design system, modeled on the Canvas LMS theming approach
  - Interactive campus map and wayfinding component
  - Accessibility standard: WCAG 2.1 AA (screen reader support, high contrast,
    keyboard and voice navigation)

Security and privacy
  - FERPA-aware data handling
  - Least-privilege credentials
  - Encryption in transit and at rest
  - Anonymized usage logging

Project management
  - Shared task list for dividing and tracking work


## 8. MAJOR MILESTONES
--------------------------------------------------------------------------------
Target dates have not been set in the project documents. Status below reflects
the work documented so far; update dates as the team schedules them.

Completed / documented
  [x] M1. Project concept and idea gathering
          (Ideas list, AI research notes, directory/map feature brainstorm)
  [x] M2. Student and faculty survey
          (33 student and 3 faculty responses; academic navigation emerged as
          the top need)
  [x] M3. Competitive landscape analysis
          (TeamDynamix, Ivy.ai/Ocelot, EAB, general AI tools; SWOT)
  [x] M4. Portfolio vision worksheet
          (purpose, guardrails, boundaries, vision statement)

Upcoming
  [ ] M5. Continued student discovery
          (interview students to decide whether wayfinding or the directory
          follows the answer engine)
  [ ] M6. Foundation build, before anything student-facing ships
          - Shared retrieval and citation service
          - Source registry
          - Evaluation test set
          - Privacy and security baseline
  [ ] M7. Mobile app shell and design system
          (Michigan Tech theme plus a universal, themeable template)
  [ ] M8. Answer engine MVP
          (chatbot with sourced answers, escalation to advisors, and feedback
          prompts)
  [ ] M9. Accessibility review
          (WCAG 2.1 AA as a release gate)
  [ ] M10. Pilot with Michigan Tech students and faculty
  [ ] M11. Follow-on products, in an order informed by student input
          (directory, wayfinding/interactive map, events feed)
  [ ] M12. Staff/admin tools
          (source registry management, analytics dashboard, theming page)
  [ ] M13. Second-institution readiness
          (configuration-only theming and onboarding)


## 9. GUARDRAILS (PRIVACY, SECURITY, ACCESSIBILITY)
--------------------------------------------------------------------------------
  - Accessibility: WCAG 2.1 AA is a release gate, not a backlog item.
  - Sourced answers only: every answer cites the official source behind it. If
    no approved source applies, the app says so and points to a person.
  - Privacy: FERPA-aware by design. No student records are stored, no data is
    sold or shared, and usage data is anonymized.
  - Security: least-privilege credentials, encryption in transit and at rest,
    and role-scoped access for anything staff-facing.
  - Human accountability: every source has a named university owner. The model
    is not the authority; the office that owns the page is.
  - Escalation: a path to a real person from anywhere in any product. No dead
    ends.
  - Transparency: users always know they are talking to an AI and are told
    when information may be out of date.


## 10. INSTALLATION INSTRUCTIONS
--------------------------------------------------------------------------------
Detailed installation steps will be added as the project nears release.
In general, setup will involve obtaining the project source code, installing
the required dependencies, configuring environment settings and credentials
for the cloud and data services, and running the application locally or on a
supported device. Refer to this section for updates as development progresses.


## 11. TEAM MEMBERS AND DEVELOPERS
--------------------------------------------------------------------------------
No team members or developers are named in the project documents provided.

  [Name] - [Role]
  [Name] - [Role]
  [Name] - [Role]

Course: MIS4100 Business Analytics & Information Systems Project
Institution: Michigan Technological University


## 12. SUPPORTING PROJECT DOCUMENTS
--------------------------------------------------------------------------------
  - UCS Competitor Analysis (competitive landscape and SWOT)
  - Portfolio Vision Worksheet (purpose, guardrails, boundaries, vision)
  - AI Research Doc (feature, data, and safeguard ideas for the chatbot)
  - Ideas for UCS (technology and design brainstorm)
  - Contact and Campus Navigation Features (directory and map feature list)
  - UCS Survey (student and faculty survey responses)

================================================================================
