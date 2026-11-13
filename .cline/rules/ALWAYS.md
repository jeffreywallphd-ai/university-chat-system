# CRITICAL RULES

## LOGGING
1. If you edit any files, place this marker before the code change "######## Cline Edit [DATE]-[FILES]" and after the code change "#### Cline Edit End". Ensure that you change the text of [DATE] to today's date AND ensure that you change [FILES] to the list of all the files you intend to change.
2. If you change or edit any files, please locate OR create the "changelog.txt" file in the /devtools root directory. After locating "changelog.txt", please enter a new line specifying: LIST OF FILES EDITED, THE PROMPT USED FOR CLINE, AND DATE.

## CODING AND DEVELOPMENT
1. If you want to use a language or technology before coding, please CHECK the tech stack list below this item AND, if the technology or language is not within the tech stack, ask before writing the code in the new language or technology.
2. Tech-Stack:  
   - Context: Here are all the technologies you'll need context for, depending on the function of the program for which you are coding:
   - Front-end: User-facing UI:  
       - React.js  
       - Typescript  
       - API List  
   - Back-end: Database  
       - MongoDB
       -  Python
3. When you are directed to change product file—and not files used for Cline (./cline/*)—ONLY modify files placed within the root's "src" folder. This directory will contain all that is needed to launch the application.
4. When you are directed to change files in ./cline, YOU MAY ONLY MODIFY FILES NOT WITHIN .cline/rules/*. Do not modify ALWAYS.md, as it is a persistent rule-set across various academic projects.

## DATA ACCESS RULEs
1. Do not modify and do not rename any of the flat storage files. These files may contain sensitive data, which would violate FERPA and destroy the viability of the project.