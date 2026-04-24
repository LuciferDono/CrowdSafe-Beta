%This is a very basic  BE PROJECT PRELIMINARY template.

%############################################# 
%#########Author :  PROJECT###########
%######### AI&DS ENGINEERING############


\documentclass[oneside,a4paper,12pt]{report}
%\usepackage{showframe}
%\hoffset = 8.9436619718309859154929577464789pt
%\voffset = 13.028169014084507042253521126761pt



\pagestyle{fancy}
\fancyhead{}
\renewcommand{\headrulewidth}{0pt}
\footskip = 0.625in
\cfoot{}
\rfoot{}

\usepackage[]{hyperref}
\usepackage{tikz}
\usetikzlibrary{arrows,shapes,snakes,automata,backgrounds,petri}
\usepackage{tikz}
\usepackage{tabularx}
\usepackage[a4paper, total={6in, 8in}]{geometry}
\usepackage[nottoc,notlot,notlof,numbib]{tocbibind}
\usepackage[titletoc]{appendix}
\usepackage{titletoc}
\renewcommand{\appendixname}{Annexure}
\renewcommand{\bibname}{References}

\setcounter{secnumdepth}


\usepackage{float}
\usepackage{subcaption}
\usepackage{multirow}

\usepackage[ruled,vlined]{algorithm2e}
\usepackage{everypage} % Ensures the border appears on all pages

% Draw border on every page
\AddEverypageHook{%
    \begin{tikzpicture}[remember picture, overlay]
        \draw[line width=2pt] 
            (current page.north west) rectangle (current page.south east);
    \end{tikzpicture}
}
\begin{document}

\pagenumbering{Roman} % Start page numbering in Uppercase Roman numerals

\setlength{\parindent}{0mm}
\begin{center}
\includegraphics[width=180pt]{DPU_DYP_Logo.png}
\\
DR.D.Y.PATIL INSTITUTE OF TECHNOLOGY  \\
\vspace{0.2cm}
PIMPRI, PUNE \\
\vspace{0.2cm}

}
{\bfseries (Affiliated to Savitribai Phule Pune University) \\}
 \vspace*{1\baselineskip}
{\bfseries A  PROJECT REPORT ON \\}
 \vspace*{2\baselineskip}
{\bfseries \fontsize{16}{12} \selectfont  CrowdSafe– Intelligent Crowd Density Monitoring \&
Stampede Prevention \\ \vspace*{1.5\baselineskip}}
{\fontsize{12}{12} \selectfont SUBMITTED TOWARDS THE PARTIAL
 \\ FULFILLMENT OF THE REQUIREMENTS OF \\

\vspace*{2\baselineskip}}
{\bfseries \fontsize{14}{12} \selectfont BACHELOR OF ENGINEERING (Artificial Intelligence and Data Science) \\
\vspace*{1\baselineskip}} 
{\bfseries \fontsize{14}{12} \selectfont BY \\ 
\vspace*{1\baselineskip}} 
Prince  \hspace{25 mm} Exam No: TAAI\&DS09 \\
Sahil Kamble\hspace{25 mm} Exam No: TAAI\&DS12  \\
Pranav Jadhav \hspace{25 mm} Exam No: TAAI\&DS70  \\
Rutvik Salve \hspace{25 mm} Exam No: TAA\&DS40 \\
\vspace*{1.5\baselineskip}
{\bfseries \fontsize{14}{12} \selectfont Under The Guidance of \\  
\vspace*{2\baselineskip}} 
Prof. Ifrah Sutar\\
\vspace{0.4cm}
\includegraphics[width=180pt]{DPU_DYP_Logo.png} \\
{\bfseries \fontsize{14}{12} \selectfont Department of Artificial Intelligence and Data Science  \\
\vspace{0.2cm}
DR.D.Y.PATIL INSTITUTE OF TECHNOLOGY \\
\vspace{0.2cm}
 A.Y 2024-2025
}
\end{center}

\newpage



\begin{figure}[ht]
\centering
\includegraphics[width=180pt]{DPU_DYP_Logo.png}
\end{figure}


{\bfseries \fontsize{14}{12} \selectfont \centerline{DR.D.Y.PATIL INSTITUTE OF TECHNOLOGY}
\vspace{0.2cm}
\centerline{Department of Artificial Intelligence and Data Science}
\vspace{0.2cm}
\vspace*{2\baselineskip}} 


{\bfseries \fontsize{16}{12} \selectfont \centerline{CERTIFICATE} 
\vspace*{2\baselineskip}} 

\centerline{This is to certify that the Project Entitled}
\vspace*{.5\baselineskip} 


{\bfseries \fontsize{14}{12} \selectfont \centerline{ CrowdSafe– Intelligent Crowd Density Monitoring \&
Stampede Prevention}
\vspace*{0.5\baselineskip}}

\centerline{Submitted by}
\vspace*{0.5\baselineskip} 
\centerline{Prince  \hspace{25 mm} Exam No:TAAI\&DS09 } 
\centerline{Sahil Kamble \hspace{25 mm} Exam No:TAAI\&DS12  } 
\centerline{Pranav Jadhav \hspace{25 mm} Exam No:TAA\&DS70 }
\centerline{Rutvik Salve \hspace{25 mm} Exam No:TAAI\&DS40 }
\\

is a bonafide work carried out by students under the supervision of Prof. Ifrah Sutar and it
is submitted towards the partial fulfillment of the requirement of Bachelor of Engineering (Artificial Intelligence and Data Science).\\
\\

\bgroup
\def\arraystretch{0.9}
\begin{tabular}{c c }
Prof. Ifrah Sutar &  \hspace{50 mm} Dr. Vaneeta Kshirsagar\\								
Internal Guide   &  \hspace{50 mm} Project Coordinator \\
%Dept. of AI and DS  &	\hspace{50 mm}Dept. of AI and DS  \\
\end{tabular}
%}
\\
\\
\\
\begin{tabular}{c c }
Dr. Mithra Venkatesan &  \hspace{50 mm} Dr. Nitin Sherje\\								
H.O. D   &  \hspace{50 mm} Principal \\
Dept. of AI and DS  &	\hspace{50 mm}DIT, Pimpri  \\
\end{tabular}
\\
\\
\\
\\
\vspace{0.2cm}
\begin{center}
%\fontsize{12}{18}\selectfont 


Name and Signature of the External Examiner
}
\end{center}
\\
%Signature of Project coordinator \hspace{15 mm} Signature of External Examiner
\newpage
\begin{center}
\textbf{PROJECT APPROVAL SHEET}
\end{center}
\begin{center}
 A Project Title
 \end{center} \\
\begin{center}
CrowdSafe– Intelligent Crowd Density Monitoring \&
Stampede Prevention
\end{center}\\
\begin{center}
Is successfully completed by 
\end{center}
\centerline{Prince  \hspace{25 mm} Exam No:TAAI\&DS09 } 
\centerline{Sahil Kamble \hspace{25 mm} Exam No:TAAI\&DS12  } 
\centerline{Pranav Jadhav \hspace{25 mm} Exam No:TAA\&DS70 }
\centerline{Rutvik Salve \hspace{25 mm} Exam No:TAAI\&DS40 }
\begin{center}
 at
 \end{center} 
 \begin{center}
 DEPARTMENT OF ARTIFICIAL INTELLIGENCE AND DATA SCIENCE
 \end{center}
 \begin{center}
 (Dr.D.Y.Patil Institute of Technology).
 \end{center}
 \begin{center}
 SAVITRIBAI PHULE PUNE UNIVERSITY,PUNE
 \end{center}
 
 \begin{center}
 ACADEMIC YEAR 2024-25
 \end{center}
 
 \vspace*{1\baselineskip}}
 \begin{tabular}{c c }
Prof. Ifrah Sutar &  \hspace{50 mm} Dr. Shubhangi Vairagar \\								
Internal Guide   &  \hspace{50 mm} H.O.D \\
Dept. of AI and DS  &	\hspace{50 mm}Dept. of AI and DS  \\
\end{tabular}
\newpage

%\pictcertificate{TITLE OF BE PROJECT}{Student Name}{Exam Seat No}{Guide Name}
\setcounter{page}{0}

\pagenumbering{Roman}
%\pictack{BE PROJECT TITLE}{Guide Name}

		
{  \newpage {\bfseries \fontsize{14}{12} \selectfont \centerline{Abstract} 
\vspace*{2\baselineskip}} \setlength{\parindent}{11mm} }
{ \setlength{\parindent}{0mm} }
The increasing crowd-related incidents that include stampedes and overcrowding and uncontrolled movement in public spaces during recent years demonstrate the urgent necessity for intelligent monitoring systems. The traditional surveillance systems base their operation on manual observation which results in inefficient operations together with high error rates and no capability to assess risks in real time. The project develops CrowdSafe which operates as an AI-powered system to monitor crowd density and prevent stampedes while it protects public safety through its automated video feed analysis system. \\

The project aims to create a smart solution which can expand to different smart environments while it detects dangerous crowd situations before they become critical. The continuous monitoring of high-density areas which include railway stations and religious gatherings and concerts and stadiums serves to prevent disasters from occurring. Human operators face challenges in monitoring multiple parameters which include density and movement patterns and behavioral anomalies at the same time. CrowdSafe uses advanced computer vision and machine learning methods to solve these problems. \\

The system employs deep learning technology to detect objects and track multiple people who move throughout a crowd. The system uses crowd analysis methods which include density estimation and velocity patterns and flow direction and spatial clustering analysis to examine crowd behavior. The system processes these metrics through a composite risk scoring mechanism which classifies situations into multiple risk levels to support timely intervention. The system enables real-time alerts together with visual feedback through its annotated video streams and dashboards which support rapid decision-making. \\

The project produces a complete operational system which enables live crowd evaluation and automatic warning system and data presentation. The system provides authorities with better situational awareness while decreasing their need to use manual observation methods. The system provides support for various video input sources which enables its use in different real-world situations. \\

CrowdSafe introduces a new system which combines four different analytical methods object detection tracking behavioral analysis and predictive risk scoring into one complete system. CrowdSafe assesses real-time crowd movements to detect early signs of stampede through its analysis of sudden crowd movements and their directional patterns. The system uses a proactive safety strategy which enhances security operations while demonstrating how AI-based surveillance technology functions in contemporary smart city systems. \\

CrowdSafe delivers a smart efficient and expandable solution for crowd control which helps create safer public spaces through its instant tracking and predictive analytics capabilities. \\

{  \newpage {\bfseries \fontsize{14}{12} \selectfont \centerline{Acknowledgments} 
\vspace*{2\baselineskip}} \setlength{\parindent}{11mm} }
{ \setlength{\parindent}{0mm} }

The preliminary project report regarding the study of {\bfseries \fontsize{12}{12} \selectfont{'CrowdSafe– Intelligent Crowd Density Monitoring \&
Stampede Prevention'}}. brings us great pleasure to present. \\

I would like to take this opportunity to thank my internal guide \textbf{Prof. Ifrah Sutar} for giving me all the help and guidance I needed. I am extremely thankful to them for providing me with ongoing assistance and support throughout the project. Their valuable suggestions and guidance helped me throughout the development of this project. \\

I am also grateful to \textbf{Dr. Shubhangi Vairagar}, Head of the Department of Artificial Intelligence and Data Science, Dr. D. Y. Patil Institute of Technology, Pimpri, for her valuable support and guidance. \\

I want to express my genuine appreciation to the Artificial Intelligence and Data Science Department faculty members who provided me with their ongoing support throughout my studies. \\

The project received essential support from various individuals who provided necessary resources including laboratory facilities and required software platforms and continuous internet access which enabled the work to be completed successfully. \\

\vspace*{3\baselineskip} \\
\begin{tabular}{p{8.2cm}c}
&Prince\\
&Sahil Kamble\\
&Pranav Jadhav\\
&Rutvik Salve\\
&(T.E. AI and DS)
%}
\end{tabular}


% \maketitle
\tableofcontents
\listoffigures 
\listoftables



\mainmatter



  \titleformat{\chapter}
\pagenumbering{arabic} % Start page numbering in Arabic numerals


\setlength{\parindent}{11mm}
\chapter{Synopsis}

\section{Project Title}
CrowdSafe– Intelligent Crowd Density Monitoring \&
Stampede Prevention
\section{ Project Option }
Internal Project

\section{Internal Guide}
Prof. Ifrah Sutar

\section{ Sponsorship and External Guide} 
This project is not sponsored by any industry. It is developed as an internal academic project under the guidance of the internal faculty. There is no external guide associated with this project.

\section{Technical Keywords (As per ACM Keywords)}
% {\bfseries Technical Key Words:}      
% \begin{itemize}
%   \item 	Cloud Computing
% \item	Service Composition
% \item	Online Web services
% \end{itemize}

Computing Methodologies
\begin{itemize}
    \item Artificial Intelligence
\end{itemize}
\begin{enumerate}
    \item Vision and Scene Understanding
    \item Object Detection
    \item Video Analysis
    \item Pattern Recognition
    \item Scene Interpretation
\end{enumerate}
\begin{itemize}
    \item Learning
\end{itemize}
\begin{enumerate}
    \item Machine Learning
    \item Deep Learning
    \item Neural Networks
\end{enumerate}

\begin{itemize}
    \item Image Processing and Computer Vision
\end{itemize}
\begin{enumerate}
    \item Scene Analysis
    \item Motion Analysis
    \item Object Tracking
    \item Spatial Clustering
\end{enumerate}

\begin{itemize}
    \item Information Storage and Retrieval
\end{itemize}
\begin{enumerate}
    \item Information Search and Retrieval
    \item Information Filtering
    \item Data Analytics
\end{enumerate}

\begin{itemize}
    \item Computer-Communication Networks
\end{itemize}
\begin{enumerate}
    \item Distributed Systems
    \item Real-time Monitoring Systems
    \item Client-Server Architecture
    \item WebSocket Communication

\end{enumerate}
\begin{itemize}
    \item Software Engineering
\end{itemize}
\begin{enumerate}
    \item Design Tools and Techniques
    \item System Architecture Design
    \item Modular Design
    \item Real-time Systems
\end{enumerate}



\section{Problem Statement}
\label{sec:problem}     
The process of handling crowd management needs for public spaces first requires tackling the unsafe situation because uncontrolled crowding leads to deadly outcomes including stampedes and injuries and fatalities. The existing surveillance systems depend on human operators who must watch several video feeds from their monitoring stations. This method shows low efficiency because it relies on human workers who make mistakes and it cannot track intricate crowd movements during active situations.\\

In sites with high population density, which include railway stations and public events and religious gatherings and stadiums, it proves challenging to monitor crowd density and track movement patterns and sudden increases in crowd size and changes in movement direction. The absence of a system that automatically detects initial indicators of hazardous situations leads to delayed responses which result in unsuccessful crowd management activities.\\

There exists a requirement for a system that uses advanced technology to monitor crowd movements while providing real-time security alerts about possible threats. The system must detect unusual crowd behavior through three specific indicators which show extreme crowd density and unexpected crowd movement and potential for stampedes.\\

\section{Abstract}

Crowd management in heavily populated regions creates its greatest challenge because uncontrolled situations can cause stampedes which result in serious accidents. The conventional systems for monitoring crowds depend on human observers who fail to provide effective detection of complex crowd activities that occur during different times of the day. The project introduces *CrowdSafe*, which functions as an advanced system for monitoring crowd density while preventing stampedes.\\

The system employs computer vision together with deep learning methods to identify and follow people through video recordings. It assesses vital metrics, which include crowd density, movement speed, flow direction, and sudden surges of people. The situation assessment process uses three factors to produce a combined risk score, which determines different safety assessment levels.\\

The system generates immediate notifications together with labeled visual outputs, which help authorities make fast decisions. The system enables users to monitor multiple video inputs while displaying all activities on one main control panel.\\

The project delivers an automated system, which scales according to needs while providing better situational awareness, and it decreases the need for human security personnel. The innovative feature combines three methods to create a system, which can detect early signs of stampedes based on three separate methods.\\

CrowdSafe improves public safety through its ability to manage crowds before they become dangerous while providing quick response capabilities.\\


\section{Goals and Objectives}
The main objective of this project is to create an advanced crowd monitoring system which operates in real time to identify dangerous crowd situations and prevent stampede events. The system uses modern AI technology together with computer vision methods to automate crowd analysis which will improve public safety.\\

The project has established its three main objectives which will be accomplished through the following activities:

\begin{itemize}
    \item The team will create a system which uses deep learning models to identify and follow people in crowded areas.
    \item The researchers will study the way crowds behave by measuring different factors which include crowd density and their movement and speed and direction of flow.
    \item The system will detect dangerous situations through its ability to recognize unexpected crowd behavior patterns which include sudden surges and overcrowding and people standing still.
    \item The researchers will create a risk assessment system which will separate crowd conditions into multiple safety categories.
    \item Authorities will receive instant alerts through our system which will help them take essential actions at the right moment.
    \item The system will display a simple to use dashboard which enables users to observe live video streams and analyze crowd behavior.
    \item The system needs to handle large camera networks which will enable organizations to expand their operations throughout their facilities.
    \item The organization seeks to reduce its need for human crowd surveillance while simultaneously enhancing the precision of its crowd monitoring process.
\end{itemize}

The project develops a system which actively monitors crowded areas while predicting possible dangers to enhance safety and operational effectiveness.

	
\section{Relevant mathematics associated with the Project}
\label{sec:math}
System Description

\begin{itemize}
    \item Input:
\end{itemize}

\begin{enumerate}
    \item Video streams from cameras (RTSP/HTTP/USB) or uploaded video files
    \item Individual video frames extracted in real-time
    \item Pixel-based spatial data (coordinates of detected persons)
\end{enumerate}

\begin{itemize}
    \item Output:
\end{itemize}
\begin{enumerate}
    \item Detected and tracked individuals with bounding boxes
    \item Crowd metrics such as count, density, velocity, and surge rate
    \item Risk score and classification (Safe, Caution, Warning, Critical)
    \item Real-time alerts and annotated video output
\end{enumerate}

\begin{itemize}
    \item Data Structures and Processing Strategies:
\end{itemize}
\begin{enumerate}
    \item Arrays and matrices for storing pixel data and detection coordinates
    \item Queues/Deques for maintaining track history and trend analysis
    \item Dictionaries/Hash maps for storing track IDs and associated attributes
    \item Graph-like structures for proximity and clustering relationships
    \item Divide-and-conquer strategy through frame-wise processing
    \item Parallel/concurrent processing using multi-threading for handling multiple camera streams simultaneously
    \item Constraints include real-time processing requirements, frame rate limits, and computational resource availability
\end{enumerate}

\begin{itemize}
    \item Functions (Mathematical and Logical Relations):
\end{itemize}
\begin{enumerate}
    \item Detection function: maps input frame → set of detected persons
    \item Tracking function: maps detected objects across frames → consistent track IDs
    \item Velocity function:
     v = distance / time
    \item Density function:
     density = number of people / area
    \item Risk function:
     R = f(density, velocity, surge, pressure, coherence)
    \item Clustering function: groups nearby points using distance-based relations (DBSCAN)
    \item Functional relations exist between input frames and computed crowd metrics
\end{enumerate}

\begin{itemize}
    \item Mathematical Formulation (if applicable):
\end{itemize}

\begin{enumerate}
    \item Euclidean Distance:
     d = √((x₂ - x₁)² + (y₂ - y₁)²)
    \item Velocity Calculation:
     v = d / t
    \item Density Estimation:
     ρ = N / A
     where N = number of people, A = area
    \item Risk Score (composite):
     R = w₁·ρ + w₂·S + w₃·(1/v) + adjustments
     where S = surge rate and w₁, w₂, w₃ are weights
    \item Flow coherence: magnitude of mean direction vectors (0 to 1 range)
\end{enumerate}

\begin{itemize}
    \item Success Conditions:
\end{itemize}
\begin{enumerate}
    \item Accurate detection and tracking of individuals in real-time
    \item Correct estimation of crowd density and movement patterns
    \item Timely generation of alerts for risky situations
    \item Smooth processing of multiple video streams without significant delay
    \item Reliable classification of crowd risk levels
\end{enumerate}
\begin{itemize}
    \item Failure Conditions:

\end{itemize}
\begin{enumerate}
    \item Incorrect detection due to occlusion, poor lighting, or camera angle
    \item Loss of tracking IDs in highly dense or fast-moving crowds
    \item Delayed or missed alerts in high-load scenarios
    \item Inaccurate risk prediction due to insufficient or noisy data
    \item System performance degradation due to hardware or network limitations
\end{enumerate}


\section{Names of Conferences / Journals where papers can be published}
\begin{itemize}
\item  IEEE/ACM Conference/Journal 1 
\item  Conferences/workshops in IITs
\item  Central Universities or SPPU Conferences 
\item IEEE/ACM Conference/Journal 2 
\end{itemize}


\section{Review of Conference/Journal Papers supporting Project idea}
\label{sec:survey}
\begin{enumerate}
    \item “Crowd Detection, Monitoring and Management: A Literature Review”\\
     This paper provides a detailed overview of various crowd monitoring techniques including detection, tracking, and behavioral analysis. It discusses traditional as well as modern approaches using computer vision and deep learning. The study highlights key challenges such as occlusion, scale variation, and dynamic crowd behavior. It emphasizes the importance of automated surveillance systems for ensuring public safety and reducing dependency on manual monitoring.
    \item “Crowd Density Detection Method Based on Multi-Column CNN”\\
     This research introduces a Multi-Column Convolutional Neural Network (M-CNN) architecture designed to estimate crowd density accurately. Different columns of the network capture features at multiple scales, making it suitable for both sparse and dense crowd scenarios. The model improves accuracy in highly congested environments and demonstrates the effectiveness of deep learning over traditional feature-based methods.
    \item “A Crowd Density Monitoring Solution Using Smart Video Surveillance”\\
     This paper presents a smart surveillance system that integrates video analytics with deep learning techniques for crowd monitoring. It focuses on real-time processing and automated density estimation. The system reduces human intervention and improves efficiency in surveillance operations, making it suitable for public safety applications such as transport hubs and large gatherings.
    \item “Crowd Monitoring System Using Image Processing”\\
     This study explores the use of classical image processing techniques such as background subtraction and motion detection for crowd analysis. It explains how crowd characteristics change based on environment and density levels. Although effective in simple scenarios, the paper highlights limitations in handling complex and highly dense crowds, thus motivating the use of advanced AI techniques.
    \item “Smart Crowd Monitoring and Suspicious Behavior Detection”\\
     This research proposes an intelligent system capable of detecting suspicious or abnormal crowd behavior using machine learning. It focuses on identifying unusual patterns such as sudden movement changes or aggressive actions. The system achieves high accuracy and reduces false alarms, demonstrating the importance of behavior analysis in addition to crowd counting.
    \item “Crowd Density Estimation Using Deep Learning for Passenger Flow”\\
     This paper focuses on estimating crowd density in transportation systems such as railway stations and exhibition centers. It uses deep learning models to analyze passenger flow and predict congestion levels. The approach helps in optimizing crowd management strategies and improving safety in high-traffic areas.
    \item “Machine Learning Techniques for Crowd Counting: A Survey”\\
     This survey paper reviews various machine learning approaches for crowd counting, including detection-based, regression-based, and density-based methods. It compares their performance, advantages, and limitations. The study highlights that deep learning techniques provide better accuracy and robustness, especially in complex environments.
    \item “Crowd Density Estimation Using CNN for Real-Time Monitoring”\\
     This research demonstrates the application of Convolutional Neural Networks for real-time crowd density estimation. It shows improved performance over traditional image processing techniques by effectively handling variations in lighting, scale, and occlusion. The system is suitable for real-time surveillance applications.
    \item “A Study on Crowd Detection and Density Analysis for Safety Control”\\
     This paper discusses the role of pattern recognition and machine learning in crowd detection and density analysis. It highlights the importance of monitoring crowd conditions to prevent accidents and improve safety. The study also explores applications in surveillance, traffic control, and event management.
    \item “ResnetCrowd: A Deep Learning Architecture for Crowd Counting and Behavior Detection”\\
     This research introduces a multi-task deep learning model based on ResNet architecture. It performs crowd counting, density classification, and violent behavior detection simultaneously. The integration of multiple tasks into a single model improves efficiency and provides a more comprehensive crowd analysis system.
    \item “DecideNet: Attention-Guided Crowd Counting and Density Estimation”\\
     This paper proposes a hybrid approach combining detection-based and regression-based methods using an attention mechanism. It dynamically selects the most suitable method based on crowd density, improving accuracy in both sparse and dense scenarios. This adaptive approach enhances robustness in real-world applications.
    \item “MRCNet: Multi-Resolution Crowd Counting and Density Estimation”\\
     This study presents a multi-resolution convolutional network designed to handle crowd counting in both aerial and ground images. It uses multi-scale feature extraction to improve accuracy and handle variations in perspective. The model is effective in complex environments where crowd density varies significantly.
\end{enumerate}
\section{Plan of Project Execution}
The CrowdSafe project develops its system through systematic execution which follows predefined phases to achieve efficient development and successful system implementation.\\

Phase 1: Problem Analysis and Requirement Gathering\\
This phase investigates the solutions to crowd management and stampede prevention problems. The system requirements, objectives, and scope of the project are defined. Relevant technologies and tools are identified.\\

Phase 2: Literature Survey and Research\\
Researchers conduct a comprehensive examination of all existing systems together with research papers that focus on crowd monitoring and object detection and computer vision. The project team examines multiple algorithms and techniques to choose the best method for their needs.\\

Phase 3: System Design\\
The system architecture establishes the complete system framework which consists of video processing and AI detection and crowd analysis and risk calculation and alert generation components. The system establishes how data will move through its components and how those components will function together.\\

Phase 4: Dataset Collection and Preparation\\
The research team collects necessary datasets and video samples which will be used for testing and validation. The research team implements preprocessing techniques which include resizing and normalization and optional annotation procedures.\\

Phase 5: Model Implementation\\
The team uses appropriate frameworks to implement deep learning models that perform object detection and tracking tasks. The team creates algorithms which will assess crowd behavior and calculate risk scores.\\

Phase 6: System Development and Integration\\
All modules are integrated into a single system. The team builds backend services and APIs together with a frontend dashboard to create an integrated system which allows users to access information through seamless communication.\\

Phase 7: Testing and Validation\\
The testing process uses different video materials to assess how well the system operates and how accurately it performs and how dependable it is. The research examines two extreme situations which involve both very crowded environments and extremely fast movements.\\

Phase 8: Deployment and Documentation\\
The final system becomes operational after it enters an appropriate deployment situation. The team produces all necessary documentation which includes the project report and user guide.\\

Phase 9: Performance Evaluation and Improvement\\
The team evaluates system performance which leads to necessary improvements that will boost accuracy and efficiency and system capacity to handle increased load.\\

\chapter{Technical Keywords}
\section{Area of Project}
The project CrowdSafe – Intelligent Crowd Density Monitoring & Stampede Prevention falls under the domain of Artificial Intelligence and Data Science, with a primary focus on Computer Vision and Machine Learning.\\
The project uses deep learning methods to detect and track objects while it uses data analysis techniques to examine how crowds behave. The project combines image processing techniques with real-time data analysis and advanced monitoring systems.\\
The system designs its modular expandable framework through software engineering practices while it creates a user-friendly monitoring and visualization interface through web development technologies. The project combines Artificial Intelligence with Computer Vision and Data Analytics and Smart Surveillance Systems to create its foundation.
\section{Technical Keywords}
% {\bfseries Technical Key Words:}      
% \begin{itemize}
%   \item 	Cloud Computing
% \item	Service Composition
% \item	Online Web services
% \end{itemize}

Computing Methodologies
\begin{itemize}
    \item Artificial Intelligence
\end{itemize}
\begin{enumerate}
    \item Vision and Scene Understanding
    \item Object Detection
    \item Video Analysis
    \item Pattern Recognition
    \item Scene Interpretation
\end{enumerate}
\begin{itemize}
    \item Learning
\end{itemize}
\begin{enumerate}
    \item Machine Learning
    \item Deep Learning
    \item Neural Networks
\end{enumerate}

\begin{itemize}
    \item Image Processing and Computer Vision
\end{itemize}
\begin{enumerate}
    \item Scene Analysis
    \item Motion Analysis
    \item Object Tracking
    \item Spatial Clustering
\end{enumerate}

\begin{itemize}
    \item Information Storage and Retrieval
\end{itemize}
\begin{enumerate}
    \item Information Search and Retrieval
    \item Information Filtering
    \item Data Analytics
\end{enumerate}

\begin{itemize}
    \item Computer-Communication Networks
\end{itemize}
\begin{enumerate}
    \item Distributed Systems
    \item Real-time Monitoring Systems
    \item Client-Server Architecture
    \item WebSocket Communication

\end{enumerate}
\begin{itemize}
    \item Software Engineering
\end{itemize}
\begin{enumerate}
    \item Design Tools and Techniques
    \item System Architecture Design
    \item Modular Design
    \item Real-time Systems
\end{enumerate}
			
\chapter{Introduction}
\section{Project Idea}
The project aims to create a system which uses artificial intelligence to control crowd movement and stop dangerous situations that lead to stampedes. CrowdSafe functions as a system which analyzes surveillance camera video feeds to find crowd-related dangers through automatic detection without requiring human input.\\
\\The system uses Artificial Intelligence and Computer Vision methods to complete three tasks which involve finding people who belong to a specific crowd and following their movements while observing how the entire crowd behaves. The system uses crowd density information together with movement data and speed measurements and directional flow patterns to detect charging events together with unusual movement patterns.\\
\\The system uses its analysis to create a risk score which divides crowd conditions into four categories that include safe and caution and warning and critical. The system alerts authorities about high-risk situations through real-time notifications which include visual information, which enables authorities to implement preventive measures.\\
\\The project develops a smart automated system which can operate in public spaces through its ability to handle automatic monitoring and assess security at railway stations and events and major public events. The system achieves its maximum efficiency through its ability to detect risks before they occur instead of waiting to respond to problems which already exist.\\

\section{Motivation of the Project}  
The project was created to address the rising incidents of stampedes and overcrowding and uncontrolled movement in public spaces which have become more frequent. Events such as religious gatherings and concerts and railway stations and festivals experience high crowd density which makes even minor disturbances capable of causing severe accidents that result in fatalities. The incidents demonstrate the urgent requirement for enhanced systems which can monitor and manage crowd behavior.\\

\\The traditional surveillance system requires human operators who need to monitor multiple camera feeds at the same time. The method becomes inefficient because it leads to human mistakes and operator exhaustion and slower reactions. A person faces extreme difficulty when trying to monitor and assess complicated crowd patterns during real-time situations.\\

\\Artificial Intelligence and Computer Vision development now enables automated crowd monitoring with early-stage risk detection capabilities. The project uses these technologies to build a smart system which will assess crowd behavior and recognize hazardous patterns while giving urgent safety notifications.\\

\\The goal is to establish preventive security measures which will identify early warning signs through monitoring activities of dangerous areas with high-rise occupancy and unexpected crowd movements. This enables authorities to take swift preventive measures which will stop accidents from happening.\\

\\The project exists to enhance public safety while decreasing human needs for surveillance through advanced technologies which build safer environments in crowded areas.\\

\vspace{5 cm}



\section{Literature Survey}
\begin{enumerate}
    \item “Crowd Detection, Monitoring and Management: A Literature Review”\\
     This paper reviews various crowd monitoring techniques including detection, tracking, and behavior analysis using computer vision and deep learning. It highlights challenges like occlusion and scale variation in dense crowds.\\
     Mathematical Terms: Density estimation (ρ = N/A), Euclidean distance, statistical analysis of crowd patterns.
    \item “Crowd Density Detection Method Based on Multi-Column CNN”\\
     This research proposes a multi-column CNN model that captures features at multiple scales for accurate crowd density estimation in both sparse and dense scenarios.\\
     Mathematical Terms: Convolution operations, feature maps, density function ∫∫ρ(x,y)dxdy, loss functions in CNN.
    \item “A Crowd Density Monitoring Solution Using Smart Video Surveillance”\\
     This paper presents a real-time surveillance system using deep learning to monitor crowd density automatically, reducing human effort and improving efficiency.\\
     Mathematical Terms: Image matrix representation, pixel intensity mapping, real-time data processing functions.
    \item “Crowd Monitoring System Using Image Processing”\\
     This study uses traditional image processing techniques like background subtraction and motion detection for crowd analysis but shows limitations in complex environments.\\
     Mathematical Terms: Frame differencing, thresholding, pixel-based segmentation, morphological operations.
    \item “Smart Crowd Monitoring and Suspicious Behavior Detection”\\
     This research focuses on detecting abnormal crowd behavior using machine learning techniques and pattern recognition, improving safety through anomaly detection.\\
     Mathematical Terms: Classification models, probability functions, anomaly detection using statistical thresholds (z-score).
    \item “Crowd Density Estimation Using Deep Learning for Passenger Flow”\\
     This paper analyzes crowd flow in transportation systems using deep learning models to predict congestion and improve management strategies.\\
     Mathematical Terms: Flow rate = people/time, density ρ = N/A, regression models for prediction.
    \item “Machine Learning Techniques for Crowd Counting: A Survey”\\
     This survey compares detection-based, regression-based, and density-based crowd counting methods, highlighting deep learning as the most effective approach.\\
     Mathematical Terms: Regression functions, probability distributions, mean squared error (MSE), statistical modeling.
    \item “Crowd Density Estimation Using CNN for Real-Time Monitoring”\\
     This research demonstrates real-time crowd density estimation using CNNs, handling variations like lighting and occlusion effectively.\\
     Mathematical Terms: Convolution layers, activation functions (ReLU), pooling operations, density integration.
    \item “A Study on Crowd Detection and Density Analysis for Safety Control”\\
     This paper emphasizes the use of pattern recognition and machine learning to monitor crowd density and improve safety in public environments.\\
     Mathematical Terms: Pattern classification, clustering algorithms, Euclidean distance formula.
    \item “ResnetCrowd: A Deep Learning Architecture for Crowd Counting and Behavior  Detection”\\
     This research introduces a ResNet-based multi-task model for crowd counting, density classification, and behavior detection simultaneously.\\
     Mathematical Terms: Residual learning (H(x) = F(x) + x), deep neural networks, loss optimization.
    \item “DecideNet: Attention-Guided Crowd Counting and Density Estimation”\\
     This paper proposes an attention-based hybrid model combining detection and regression approaches for improved accuracy across varying densities.\\
     Mathematical Terms: Attention weights, weighted sum functions, hybrid modeling, optimization functions.
    \item “MRCNet: Multi-Resolution Crowd Counting and Density Estimation”\\
     This study uses multi-resolution CNNs to capture features at different scales, improving performance in complex environments with varying crowd densities.\\
     Mathematical Terms: Multi-scale feature extraction, convolution operations, spatial resolution mapping.
\end{enumerate}


\chapter{Problem Definition and scope}
\section{Problem Statement}

The process of handling crowd management needs for public spaces first requires tackling the unsafe situation because uncontrolled crowding leads to deadly outcomes including stampedes and injuries and fatalities. The existing surveillance systems depend on human operators who must watch several video feeds from their monitoring stations. This method shows low efficiency because it relies on human workers who make mistakes and it cannot track intricate crowd movements during active situations.\\

In sites with high population density, which include railway stations and public events and religious gatherings and stadiums, it proves challenging to monitor crowd density and track movement patterns and sudden increases in crowd size and changes in movement direction. The absence of a system that automatically detects initial indicators of hazardous situations leads to delayed responses which result in unsuccessful crowd management activities.\\

There exists a requirement for a system that uses advanced technology to monitor crowd movements while providing real-time security alerts about possible threats. The system must detect unusual crowd behavior through three specific indicators which show extreme crowd density and unexpected crowd movement and potential for stampedes.\\

\vspace{5 cm}

\subsection{Goals and objectives}  
Goal and Objectives: 
The main objective of this project is to create an advanced crowd monitoring system which operates in real time to identify dangerous crowd situations and prevent stampede events. The system uses modern AI technology together with computer vision methods to automate crowd analysis which will improve public safety.\\

The project has established its three main objectives which will be accomplished through the following activities:

\begin{itemize}
    \item The team will create a system which uses deep learning models to identify and follow people in crowded areas.
    \item The researchers will study the way crowds behave by measuring different factors which include crowd density and their movement and speed and direction of flow.
    \item The system will detect dangerous situations through its ability to recognize unexpected crowd behavior patterns which include sudden surges and overcrowding and people standing still.
    \item The researchers will create a risk assessment system which will separate crowd conditions into multiple safety categories.
    \item Authorities will receive instant alerts through our system which will help them take essential actions at the right moment.
    \item The system will display a simple to use dashboard which enables users to observe live video streams and analyze crowd behavior.
    \item The system needs to handle large camera networks which will enable organizations to expand their operations throughout their facilities.
    \item The organization seeks to reduce its need for human crowd surveillance while simultaneously enhancing the precision of its crowd monitoring process.
\end{itemize}

The project develops a system which actively monitors crowded areas while predicting possible dangers to enhance safety and operational effectiveness.


 \subsection{Statement of scope} 

The project CrowdSafe – Intelligent Crowd Density Monitoring & Stampede Prevention aims to create an artificial intelligence system which will track real-time crowd conditions through video monitoring. The system can identify and follow people while it studies crowd movements to discover dangerous situations which emerge from excessive crowding and unexpected waves of people and unusual flow behavior.\\

The project covers the implementation of computer vision and machine learning techniques for crowd detection, tracking, density estimation, and behavior analysis. The project includes the creation of a risk assessment model which divides crowd situations into multiple safety categories while producing warnings for extreme danger situations. The system provides users with an accessible dashboard which enables them to see and track system activities.\\

The application is designed for operation within controlled settings which include public surveillance camera streams from railway stations and events and campus areas. The system enables users to process multiple video feeds in real time while operating within the boundaries of existing computing power.\\

The project only permits video analysis as its primary method since it does not include hardware sensors or ability to analyze entire urban areas. The system exhibits performance fluctuations which depend on camera quality and lighting conditions and crowd density. The existing scope does not include advanced predictive modeling which extends beyond short-term analysis.\\

The project implements a practical solution which can be expanded across different operational areas to monitor crowds while improving safety measures.\\


\vspace{5 cm}

\section{Major Constraints}
\begin{itemize}
    \item The CrowdSafe system development process together with its implementation face multiple restrictions which will affect the software development process through its specification and design and implementation and testing.
     
    \item The primary constraint for the project exists in computational resources, because real-time video processing and deep learning models need processing power together with memory resources. The system will experience decreased performance together with slower response times because its hardware capabilities remain restricted.
     
    \item The system encounters an essential restriction through video quality and environmental conditions. Detection accuracy suffers due to factors which include poor lighting conditions and low-resolution camera systems together with occlusion and camera angle changes.
     
    \item The system requires network bandwidth and connectivity to operate correctly during multiple camera streaming and real-time data transmission tasks. Live monitoring together with alert generation will experience disruptions due to network delays or interruptions.
     
    \item The system performance depends on data availability and dataset limitations which create barriers to effective operation. The lack of diverse and high-quality datasets will limit the model's capacity to adapt successfully to various real-world situations.
     
    \item The system experiences real-time processing constraints which require it to achieve both precise results and rapid operational speed. The execution of high accuracy models will extend computation durations which will hinder real-time operation.
     
    \item The system experiences scalability constraints because its expansion to multiple cameras and large spaces requires effective resource handling and system performance optimization.

    \item Video surveillance systems create security and privacy concerns because they deal with sensitive information that needs secure access and protection protocols. 
     
    \item The system needs to eliminate these restrictions because they affect its capacity to function efficiently while maintaining its reliability and suitability for actual operational use.
\end{itemize}

\section{Methodologies of Problem solving and efficiency issues}
\begin{itemize}
    \item The problem of crowd monitoring and stampede prevention can be addressed through different methods which produce various results and have different efficiency levels.
     
    \item The traditional method uses image processing techniques which estimate crowd presence through background subtraction and edge detection and motion detection methods.
     
    \item The methods operate with low computational needs because they require minimal processing resources, but their performance declines with complex environments that include occluded areas and different lighting conditions and high crowd density.
     
    \item The second method uses machine learning techniques where specific features get extracted from images to perform crowd classification or counting tasks. The methods achieve better accuracy results than traditional techniques because they utilize automated detection methods. The system needs human experts to create specific features, which limits their performance across different situations.
     
    \item Deep learning-based methods emerge as the most effective solution, whereas Convolutional Neural Networks (CNNs) serve as the optimal solution for object detection and density estimation tasks. The YOLO model enables real-time detection, which maintains high accuracy, while multi-object tracking algorithms ensure continuous individual tracking throughout multiple frames. These methods demonstrate strong performance capabilities when applied to intricate situations that involve highly crowded environments.
     
    \item Crowd movement analysis employs clustering techniques which use DBSCAN to detect patterns and anomalies through velocity computation and flow analysis methods. The system detects dangerous situations through these methods, which identify preliminary indicators of emerging threats.
     
    \item The efficiency of a system depends on its need to balance two conflicting requirements, which are precise results and the expenses of performing calculations. Deep learning models provide precise results, yet they need extensive computing power, while basic methods deliver quicker results, but their accuracy suffers. The system achieves performance equilibrium through optimal control of three system parameters, which include model size and processing resolution and frame rate.
     
    \item The system achieves efficiency through its implementation of parallel and concurrent processing methods, which enable simultaneous processing of multiple video streams through multi-threading technology. The system uses selective processing methods, which include frame skipping and resolution scaling, to decrease the processing demands of the system while maintaining system accuracy.
     
    \item The selected methodology integrates deep learning with processing optimization methods, which enable the system to deliver both real-time performance and high accuracy through its application in actual operational environments.
\end{itemize}


\section{Outcome}
\begin{itemize}
     
    \item The project CrowdSafe – Intelligent Crowd Density Monitoring \& Stampede Prevention produces a complete system which uses video feeds to track crowd situations throughout different times. The system successfully detects and tracks individuals, estimates crowd density, and analyzes movement patterns to identify potential risk situations.
     
    \item The implemented system generates a composite risk score based on multiple parameters such as density, velocity, and crowd behavior, and classifies the situation into different safety levels. The system uses video streams and dashboard tools to deliver real-time alerts which show visual information to help authorities make timely preventive actions.
     
    \item The project provides better monitoring results because it uses automated systems to track people instead of needing human operators who work directly with the monitored area. The system decreases need for human operators while it shortens time needed for response and improves understanding of situations which happen in crowded areas.
     
    \item The system enables users to handle different video feeds while it adapts to multiple real-life situations which occur in public spaces and transportation centers and major events. The successful integration of detection, tracking, and behavior analysis highlights the effectiveness of AI-based solutions in crowd management.
    
    \item The project delivers a scalable and intelligent solution which improves public space safety through its ability to monitor locations and detect emerging hazards.
\end{itemize}

\section{Applications}
\begin{itemize}
     
    \item The CrowdSafe system operates in multiple fields that require effective monitoring and management of large public gatherings.
     
    \item The system functions to track passenger movement and stop overcrowding in railway stations and bus terminals and airports. The system helps handle large crowds at public events such as concerts and festivals and sports events by finding dangerous situations before they happen.
     
    \item The system applies to religious gatherings and pilgrimage sites because both locations experience high attendance which increases the danger of stampedes. The system enables public safety improvements through surveillance system connections which help cities handle crowd movement better.
     
    \item CrowdSafe enables shopping centers to track customer movement patterns while managing customer traffic throughout their premises. The system provides support for emergency evacuation planning because it requires knowledge of how crowds will move during emergencies.
     
    \item The system enables law enforcement and security agencies to forecast crowd behavior through its continuous monitoring of crowd movements. The system functions as a tool for both traffic and pedestrian monitoring systems which helps control traffic buildup in heavily traveled regions.
     
    \item The project creates a flexible solution that enables organizations to enhance safety and operational efficiency and handle crowd control in different real-world situations.
\end{itemize}

\vspace{3 cm}

\section{Hardware Resources Required}
\begin{table}[!htbp]
\begin{center}
\def\arraystretch{1.5}
\resizebox{\textwidth}{!}{
\begin{tabular}{| c | c | p{4cm} | p{5cm} |}
\hline
Sr. No. & Parameter & Minimum Requirement & Justification \\
\hline
1 & CPU Speed & 2.5 GHz (Intel i5 or above) & Required for efficient real-time video processing and AI computations \\
\hline
2 & RAM & 8 GB & Needed to handle multiple video streams and model execution smoothly \\
\hline
3 & Storage & 256 GB SSD & Required for storing datasets, recordings, and application files \\
\hline
4 & GPU (Optional) & NVIDIA GPU with CUDA support & Enhances performance of deep learning models and speeds up processing \\
\hline
5 & Camera/Input Device & CCTV/IP Camera/Webcam & Required to capture live video feed for analysis \\
\hline
6 & Network & Stable Internet Connection & Needed for streaming, data transmission, and dashboard access \\
\hline
\end{tabular}
}
\end{center}
\caption{Hardware Requirements}
\label{tab:hreq}
\end{table}


\section{Software Resources Required}
Platform : 
\begin{itemize}
    \item Operating System (Windows/Linux/macOS)
    \item Python 3.10 or above
    \item Flask / Streamlit
    \item PyTorch / TensorFlow
    \item OpenCV
    \item SQLite / PostgreSQL
    \item VS Code / PyCharm
\end{itemize}




\chapter{Project Plan}

\section{Project Estimates}
                 Use Waterfall model and associated streams derived from assignments 1,2, 3, 4 and 5( Annex A and B) for estimation. 
\subsection{Reconciled Estimates}
\subsubsection{Cost Estimate}

\subsubsection{Time Estimates}


\subsection{Project Resources}
          Project resources  [People, Hardware, Software, Tools and other resources] based on Memory Sharing, IPC, and Concurrency derived using appendices to be referred. 

\section{Risk Management w.r.t. NP Hard analysis}
This section discusses Project risks and the approach to managing them.
\subsection{Risk Identification}
For risks identification, review of scope document, requirements specifications and schedule is done. Answers to questionnaire revealed some risks. Each risk is categorized as per the categories mentioned in \cite{bookPressman}. Please refer table \ref{tab:risk} for all the risks. You can refereed following risk identification questionnaire.

\begin{enumerate}
\item Have top software and customer managers formally committed to support the project?
\item Are end-users enthusiastically committed to the project and the system/product to be built?
\item Are requirements fully understood by the software engineering team and its customers?
\item Have customers been involved fully in the definition of requirements?
\item Do end-users have realistic expectations?
\item Does the software engineering team have the right mix of skills?
\item Are project requirements stable?
\item Is the number of people on the project team adequate to do the job?
\item Do all customer/user constituencies agree on the importance of the project and on the requirements for the system/product to be built?
\end{enumerate}

\subsection{Risk Analysis}
The risks for the Project can be analyzed within the constraints of time and quality

\begin{table}[!htbp]
\begin{center}
%\def\arraystretch{1.5}
\def\arraystretch{1.5}
\begin{tabularx}{\textwidth}{| c | X | c | c | c | c |}
\hline
\multirow{2}{*}{ID} & \multirow{2}{*}{Risk Description}	& \multirow{2}{*}{Probability} & \multicolumn{3}{|c|}{Impact} \\ \cline{4-6}
	& & &	Schedule	& Quality	& Overall \\ \hline
1	& Description 1	& Low	& Low	& High	& High \\ \hline
2	& Description 2	& Low	& Low	& High	& High \\ \hline
\end{tabularx}
\end{center}
\caption{Risk Table}
\label{tab:risk}
\end{table}


\begin{table}[!htbp]
\begin{center}
%\def\arraystretch{1.5}
\def\arraystretch{1.5}
\begin{tabular}{| c | c | c |}
\hline
Probability & Value &	Description \\ \hline
High &	Probability of occurrence is &  $ > 75 \% $ \\ \hline
Medium &	Probability of occurrence is  & $26-75 \% $ \\ \hline
Low	& Probability of occurrence is & $ < 25 \% $ \\ \hline
\end{tabular}
\end{center}
\caption{Risk Probability definitions \cite{bookPressman}}
\label{tab:riskdef}
\end{table}

\begin{table}[!htbp]
\begin{center}
%\def\arraystretch{1.5}
\def\arraystretch{1.5}
\begin{tabularx}{\textwidth}{| c | c | X |}
\hline
Impact & Value	& Description \\ \hline
Very high &	$> 10 \%$ & Schedule impact or Unacceptable quality \\ \hline
High &	$5-10 \%$ & Schedule impact or Some parts of the project have low quality \\ \hline
Medium	& $ < 5 \% $ & Schedule impact or Barely noticeable degradation in quality Low	Impact on schedule or Quality can be incorporated \\ \hline
\end{tabularx}
\end{center}
\caption{Risk Impact definitions \cite{bookPressman}}
\label{tab:riskImpactDef}
\end{table}

\subsection{Overview of Risk Mitigation, Monitoring, Management}


Following are the details for each risk.
\begin{table}[!htbp]
\begin{center}
%\def\arraystretch{1.5}
\def\arraystretch{1.5}
\begin{tabularx}{\textwidth}{| l | X |}
\hline 
Risk ID	& 1 \\ \hline
Risk Description	& Description 1 \\ \hline
Category	& Development Environment. \\ \hline
Source	& Software requirement Specification document. \\ \hline
Probability	& Low \\ \hline
Impact	& High \\ \hline
Response	& Mitigate \\ \hline
Strategy	& Strategy \\ \hline
Risk Status	& Occurred \\ \hline
\end{tabularx}
\end{center}
%\caption{Risk Impact definitions \cite{bookPressman}}
\label{tab:risk1}
\end{table}

\begin{table}[!htbp]
\begin{center}
%\def\arraystretch{1.5}
\def\arraystretch{1.5}
\begin{tabularx}{\textwidth}{| l | X |}
\hline 
Risk ID	& 2 \\ \hline
Risk Description	& Description 2 \\ \hline
Category	& Requirements \\ \hline
Source	& Software Design Specification documentation review. \\ \hline
Probability	& Low \\ \hline
Impact	& High \\ \hline
Response	& Mitigate \\ \hline
Strategy	& Better testing will resolve this issue.  \\ \hline
Risk Status	& Identified \\ \hline
\end{tabularx}
\end{center}
\label{tab:risk2}
\end{table}

\begin{table}[!htbp]
\begin{center}
%\def\arraystretch{1.5}
\def\arraystretch{1.5}
\begin{tabularx}{\textwidth}{| l | X |}
\hline 
Risk ID	& 3 \\ \hline
Risk Description	& Description 3 \\ \hline
Category	& Technology \\ \hline
Source	& This was identified during early development and testing. \\ \hline
Probability	& Low \\ \hline
Impact	& Very High \\ \hline
Response	& Accept \\ \hline
Strategy	& Example Running Service Registry behind proxy balancer  \\ \hline
Risk Status	& Identified \\ \hline
\end{tabularx}
\end{center}
\label{tab:risk3}
\end{table}

\section{Project Schedule}  
\subsection{Project task set}  
Major Tasks in the Project stages are:
\begin{itemize}
  \item Task 1:
  \item Task 2: 
  \item Task 3: 
  \item Task 4: 
  \item Task 5: 
\end{itemize}

\subsection{Task network}  
Project tasks and their dependencies are noted in this diagrammatic form.
\subsection{Timeline Chart}  
A project timeline chart is presented. This may include a time line for the entire project.
Above points should be covered  in Project Planner as Annex C and you can mention here Please refer Annex C for the planner

 
\section{Team Organization}
The manner in which staff is organized and the mechanisms for reporting are noted.  
\subsection{Team structure}
The team structure for the project is identified. Roles are defined.

\subsection{Management reporting and communication}
Mechanisms for progress reporting and inter/intra team communication are identified as per assessment sheet and lab time table. 
 
\chapter{Software requirement specification  }

\section{Introduction}

The Software Requirement Specification (SRS) for the project “CrowdSafe – Intelligent Crowd Density Monitoring \& Stampede Prevention” defines the overall structure, functionality, and requirements of the system to be developed. The document provides a complete system overview that developers and designers and stakeholders can use to understand the system objectives and system features and system operation patterns.\\

The CrowdSafe system uses video inputs and advanced AI techniques to monitor crowd conditions in real time. The system uses AI technology to detect individuals and analyze crowd behavior and estimate density and identify potential risk situations through overcrowding and sudden movement surges.\\

This section provides an introduction to the purpose, scope, and responsibilities involved in the development of the system. The process establishes clear system requirements and expected outcomes to all stakeholders which helps decrease development process uncertainties.\\


\subsection{Purpose and Scope of Document}
The Software Requirement Specification document defines functional and non-functional requirements of the CrowdSafe system which operates Intelligent Crowd Density Monitoring and Stampede Prevention. The document provides developers designers and stakeholders a formal reference which describes system features and system limitations and system performance expectations.\\

The document presents system architecture together with input specifications output specifications user interaction methods and system performance metrics. The process development process maintains proper structure through this document which meets project goals.\\

The document describes the design and implementation of an AI-based system which processes video feeds to identify and monitor people while it evaluates crowd movements and calculates density and issues risk warnings. The system requires development of a user interface which enables monitoring and visual representation of data.\\

The project scope restricts itself to software-based crowd monitoring which uses video inputs and excludes all hardware integrations and large-scale system deployment requirements. The document focuses on providing a clear understanding of the system requirements to support efficient development and testing.\\

\subsection{Overview of responsibilities of Developer}
The CrowdSafe system requires the developer to execute tasks which cover system design, implementation, testing, and maintenance. The team must build essential system components which include video processing and object detection and tracking and crowd estimation and risk assessment and warning system development.\\

The developer must ensure that the system meets all specified functional and non-functional requirements. The work requires the development of high-performance code which connects system components while maintaining effective communication between backend systems and user interface elements.\\

The developer must develop machine learning systems and computer vision systems to enable precise identification and study of crowd patterns. The developer handles data processing tasks while he/she oversees database operations and manages system data storage and retrieval processes.\\

The developer must test the system and debug it to confirm that all system functions operate correctly in various testing scenarios. The developer must create a system which delivers optimal performance during actual operational conditions.\\

The developer must create system documentation which consists of code documentation and user manuals to facilitate comprehension and future system upkeep. The developer maintains system reliability through his/her work on system efficiency and scalability development tasks.\\

\section{Usage Scenario}
The section provides an explanation of different situations in which the CrowdSafe system operates because it demonstrates the system's functionality through actual field testing. The system operates primarily in locations where people assemble in large numbers, which include railway stations and stadiums and public events and religious sites.\\

The system receives its video input from surveillance cameras which capture live video streams. The system processes the video in real time to detect and track individuals, analyze crowd density, and monitor movement patterns. The system uses this analysis to assess the risk level that corresponds with the existing crowd situation.\\

The system generates alerts together with monitoring dashboard warnings when it identifies dangerous behavior which includes both overcrowding and sudden movement surges and irregular flow patterns. The authorities and operators can take immediate measures to control the situation and stop upcoming dangers from happening.\\

The system allows post-event analysis through its ability to examine recorded data and metrics, which supports better event planning and decision-making processes for upcoming events. The system usage scenarios show how the system enables advance crowd control methods while delivering safer experiences in crowded spaces.\\

\subsection{User profiles}  
The CrowdSafe system needs different user groups who have designated duties to operate and maintain its functions:\\

1. Admin:\\
The admin system functions as the highest authority of the system because it allows complete system access. The admin controls user management system settings and camera installations while watching how the system performs. The admin must establish system security measures while validating that all system components operate effectively.\\

2. Operator:\\
The operator monitors live video streams while using the dashboard to track crowd movement. The system generates alerts which operators use to control crowd management operations. In real-time operations operators use the system to perform their duties.\\

3. Viewer:\\
The viewer role provides restricted system access which allows users to watch live feeds and view basic analytics without system modification rights. This role is typically assigned to stakeholders or authorities who need visibility but not control.\\

User profiles define specific access rights which protect system security and enable efficient system operation and control of user activities.

\vspace{10 cm}

\subsection{Use-cases}
All use-cases for the software are presented. Description of all main Use cases using use case template is to be provided.
\begin{table}[!htbp]
\begin{center}
\def\arraystretch{1.3}
\resizebox{\textwidth}{!}{
\begin{tabular}{| c | c | p{5cm} | c | p{5cm} |}
\hline
Sr No. & Use Case & Description & Actors & Assumptions \\
\hline
1 & User Login & User logs into the system using valid credentials & Admin, Operator, Viewer & User has valid login credentials \\
\hline
2 & Add Camera & Admin adds a new camera or video source to the system & Admin & Camera source is available and accessible \\
\hline
3 & Start Monitoring & System starts processing video feed and analyzing crowd & Admin, Operator & Camera is active and system is running \\
\hline
4 & Detect Crowd & System detects and tracks individuals in the video & System & Video input is clear and available \\
\hline
5 & Analyze Crowd Behavior & System analyzes crowd density, movement, and flow patterns & System & Sufficient number of people detected \\
\hline
6 & Generate Alert & System generates alerts for abnormal or risky situations & System & Risk threshold is exceeded \\
\hline
7 & View Dashboard & User views real-time data, alerts, and analytics & Admin, Operator, Viewer & System is actively running \\
\hline
8 & Stop Monitoring & User stops the video processing and monitoring & Admin, Operator & System is currently running \\
\hline
\end{tabular}
}
\end{center}
\caption{Use Cases}
\label{tab:usecase}
\end{table}

\vspace{10 cm}

\subsection{Use Case View}
\begin{center}
	\begin{figure}[!htbp]
		\centering
		\fbox{\includegraphics[width=\textwidth]{use case diagram.png}}
	  \caption{Use case diagram}
	  \label{fig:usecase}
	\end{figure}
\end{center}  

\vspace{5 cm}


\section{Data Model and Description}  

The CrowdSafe system data model establishes the methods which the application organizes its data and keeps its information and handles its data. The system description shows how data entities are structured through their data attributes and their connections to other entities. The model enables effective data operations which function through continuous processing and analysis in real time.\\

The system handles multiple data categories which include video input data and detected object information and crowd metrics and alerts and user-related data. The system processes these data elements through continuous operations while they get stored in a structured format which enables monitoring and analysis and reporting activities.\\

The data model enables the system to handle multiple camera inputs and large data volumes because of its design which allows both scalability and flexible operation. The system maintains data consistency and integrity which organizations need to perform accurate crowd analysis and make informed decisions.\\

The data model serves as a base which the system uses to apply effective data organization methods while enabling different CrowdSafe system modules to work together without problems.

\subsection{Data Description}  

The CrowdSafe system manages and processes various types of data required for real-time crowd monitoring and analysis. The system receives its main operational input through video streams which it collects from cameras to process each frame individually.\\

The system uses video frames to gather critical information about detected people together with their current locations (coordinates) and their moving patterns and tracking identification numbers. The system uses this information to calculate different parameters about crowds which include total crowd size and crowd density and crowd movement speed and direction of crowd movement.\\

The system creates analytical information which includes risk assessment scores and risk assessment levels and alert notification details based on its assessment of crowd control situations. The system stores all its generated outputs in structured database formats which users can access for immediate use or future retrieval.\\

The system keeps track of all user information which includes their login information and their different access rights (admin, operator, viewer) while also storing system configuration information which contains camera specifications and operational parameters.\\

The system processes all necessary data through input video files together with processed analytical results and system alerts and user data which all work together to enable the effective operation of the CrowdSafe platform.\\


\subsection{Data objects and Relationships}
The CrowdSafe system uses its main data components to create effective crowd monitoring and analysis capacities through their interconnected function. The system's main data components serve as its basic system entities which determine how data moves between the various system components.\\

The primary data objects include User, Camera, Video Frame, Detection, Metrics, and Alert. The User object stores information related to system users such as admin, operator, and viewer, along with their roles and credentials. The Camera object contains details of video sources such as camera ID, location, and stream URL.\\

The system processes all Video Frames which each camera produces through its operations. From these frames, Detection objects are created, which show the identified individuals through their tracking IDs and position data. The system uses these detections to calculate Metrics which include crowd count, density, velocity, and risk level.\\

The system uses metric analysis results to create Alert objects which identify abnormal conditions and risky situations. Alerts are linked to specific cameras and time instances, and they are used to notify users.\\

The object relationships show that users control multiple cameras which generate multiple video frames from each camera, while each frame creates multiple detections, which lead to metric calculations through detections, and metrics exceed thresholds to produce alert notifications. The established data object relationship structure creates conditions that support seamless data movement through the system, which leads to precise data analysis and optimal system operation.




 
 
\section{Functional Model and Description}  

The CrowdSafe system functional model demonstrates its primary system operations together with their component functionality requirements which enable the system to achieve its intended results. It shows how data moves through various stages for processing during crowd monitoring and analysis.\\

The system starts its operation by recording video footage which comes from both camera sources and user-uploaded materials. The system uses computer vision methods to process video input through its frames to find and follow people in the footage. The system uses detected information to determine various crowd characteristics which include total count, crowd density, movement speed, and distribution of movements.\\

The system uses a predefined risk model to determine risk levels based on calculated parameters. The system activates alerts and notifications when it detects abnormal situations that include both overcrowding and rapid crowd increases and unexpected flow changes.\\

The functional model shows all user interaction activities which include system login, dashboard access, live feed monitoring, and camera system control. The system handles each function through real-time execution which maintains operational efficiency while connecting different system components together.\\

The functional model shows how the system receives input data and conducts analysis to produce results which enable effective crowd monitoring and decision-making.

\vspace{5 cm}

\subsection{Data Flow Diagram}  
\subsubsection{Level 0 Data Flow Diagram}

 

\usepackage{}  % in preamble
\begin{figure}[H]
\centering
\includegraphics[width=1\textwidth]{level 0 data flow diagram.png}
\caption{Level 0 Data Flow Diagram}
\end{figure}

\vspace{1 cm}
\subsubsection{Level 1 Data Flow Diagram}

\usepackage{}
\begin{figure}[H]
\centering
\includegraphics[width=1.1\linewidth]{level 1 data flow diagram.png}
\caption{Level 1 Data FLow Diagram}
\end{figure}

\vspace{3 cm}
\subsection{Activity Diagram:}
\begin{itemize}
	\item	The Activity diagram represents the steps taken.
\end{itemize} 

\usepackage{}
\begin{figure}[H]
\centering
\includegraphics[width=1\linewidth]{activity diagram.png}
\caption{Activity Diagram}
\end{figure}


\subsection{Non Functional Requirements:}
Non-functional requirements define the quality attributes and constraints of the CrowdSafe system. These requirements ensure that the system performs efficiently, reliably, and securely under different conditions.\\

• Interface Requirements:\\
The system provides a user-friendly web-based interface that allows users to interact with the application easily. The dashboard displays live video feeds, crowd metrics, alerts, and system status. The interface is designed to be responsive and accessible across different devices such as desktops and laptops. It ensures smooth interaction between users and system functionalities.\\

• Performance Requirements:\\
The system is required to process video streams in real time with minimal latency. It should handle multiple camera inputs simultaneously without significant performance degradation. Efficient memory and CPU utilization must be maintained to ensure smooth execution. The system should provide quick response times for user actions and alert generation.\\

• Software Quality Attributes:\\

\begin{enumerate}

\item Availability (Reliability):\\
    The system should be available for continuous operation with minimal downtime. It must handle failures gracefully and ensure consistent performance.\\
    
\item Modifiability:\\
    The system should be designed in a modular way to allow easy updates and enhancements.\\
    
    Portability: The system should run on different operating systems with minimal changes.\\
    Reusability: Components should be reusable across different modules or projects.\\
    Scalability: The system should support the addition of multiple cameras and increased data load.\\

\item Performance:\\
The system should maintain high accuracy and efficiency in processing and analyzing crowd data in real time.

\item Security:\\
The system should ensure secure user authentication and data protection. Access control mechanisms should be implemented to restrict unauthorized access.\\

\item Testability:\\
The system should be easy to test, with clearly defined modules and functionalities that can be validated independently.\\

\item Usability:\\
The system should be easy to use with a simple and intuitive interface.\\

    Self Adaptability: The system should adjust to varying input conditions such as different crowd densities.\\
    User Adaptability: The interface should be easy to understand for different types of users (admin, operator, viewer).\\

\end{enumerate}
Overall, these non-functional requirements ensure that the CrowdSafe system is efficient, reliable, secure, and user-friendly.

\vspace{6 cm}
\subsection{State Diagram:}	


\begin{center}
	\begin{figure}[!htbp]
		\centering
		\fbox{\includegraphics[width=1\linewidth]{state diagram.png}}
	  \caption{State transition diagram}
	  \label{fig:state-dig}
	\end{figure}
\end{center} 
 
 \subsection{Design Constraints}	
 
The design restrictions of the CrowdSafe system establish all its operational boundaries and design limitations. The system requires these constraints to be evaluated because they determine its practical operation and efficient performance and resource availability.\\

The system requires hardware resources because real-time video processing depends on high-performance computing. The system design must be optimized to run efficiently on systems with limited CPU, memory, or GPU capabilities.\\

The system needs to process video streams in real time, which creates another requirement because it needs to analyze video streams with minimal delay. This task requires the development of both efficient algorithms and optimized data management methods.\\

The system detection capabilities are limited by the camera capabilities and the environmental factors including lighting conditions and resolution and occlusion. The design needs to incorporate these variations to sustain operational effectiveness.\\

The system needs to handle multiple camera inputs without performance loss because it needs to support multiple camera inputs without performance loss. Proper architecture design is required to handle increasing data loads.\\

The network constraints of bandwidth and latency restrict the delivery of video streams and alerts especially when operating in distributed systems.\\

The system needs to implement security and privacy measurements which protect user data and video feeds while controlling access to authorized personnel only.\\

The design constraints of the project determine how CrowdSafe system design will develop through its architectural development and system implementation process.\\

\subsection{Software Interface Description}	 

The CrowdSafe system interacts with multiple external components which include users and hardware devices and software services. This section describes the interfaces through which the system communicates with the outside world.\\

The primary interface of the system functions as a user interface which operates through a web-based dashboard that developers built using Streamlit and Flask frameworks. The system enables users in three roles (admin operator and viewer) to log in and monitor live video streams and access crowd analytics and receive notifications. The interface provides users with an intuitive design that responds to their actions while allowing them to navigate the system easily.\\

The system establishes connections with camera devices which include CCTV cameras and IP cameras and webcams. The system receives real-time video streams which the devices send to him. The interface supports standard protocols which include RTSP and HTTP to enable video streaming.\\

The system connects with backend services and databases to handle user data storage and detection result storage and metric storage and alert storage. The database system uses SQLite and PostgreSQL to handle structured data management tasks.\\

The system has the capability to connect with external notification services which allow it to dispatch alerts through email and SMS and in-app notifications. This system guarantees that users receive essential information during crucial moments.\\

The system depends on software libraries and frameworks which include OpenCV and PyTorch and TensorFlow to provide its image processing and deep learning capabilities. The system uses these interfaces to perform its core analytical functions.\\

The software interfaces enable system communication with external entities which leads to effective data transfer and system functionality.


\chapter{Detailed Design Document using Appendix A and B}
 \section{Introduction}  
This document specifies the design that is used to solve the problem of Product.  
\section{Architectural Design}  
	A description of the program architecture is presented. Subsystem design or Block diagram,Package Diagram,Deployment diagram with description is to be presented.

 
  \begin{center}
	\begin{figure}[!htbp]
		\centering
		\fbox{\includegraphics[width=1\textwidth]{arch2.jpg}}
	  \caption{Architecture diagram}
	  \label{fig:arch-dig}
	\end{figure}
\end{center} 


\section{Data design (using Appendices A and B)}   
A description of all data structures including internal, global, and temporary data structures, database design (tables), file formats.
\subsection{Internal software data structure}
Data structures that are passed among components the software are described.
\subsection{Global data structure}
Data structured that are available to major portions of the architecture are described.
\subsection{Temporary data structure}
Files created for interim use are described.
\subsection{Database description}
Database(s) / Files created/used  as part of the application is(are) described.


\section{Compoent Design} 
Class diagrams, Interaction Diagrams, Algorithms. Description of each component description required.
\subsection{Class Diagram}
 \begin{center}
	\begin{figure}[!htbp]
		\centering
		\fbox{\includegraphics[width=450pt]{class-dig.jpg}}
	  \caption{Class Diagram}
	  \label{fig:class-dig}
	\end{figure}
\end{center} 
 
\chapter{Project Implementation}

\section{Introduction}

Once the design was locked, we shifted to building the actual system. The goal was not to write clever code for the sake of it — the goal was to get a live video feed analysed, risk-scored, and displayed on a browser dashboard in real time, reliably, without crashes. That is harder than it sounds. We went through several failed approaches before we arrived at the architecture described here.

The final system is divided into three clear concerns. The AI layer handles detection and tracking. The analytics layer computes the crowd behaviour signals. The API and delivery layer puts those signals in front of operators through a Flask web server and SocketIO-based WebSocket stream. Each concern is implemented as its own Python module, which made debugging individual pieces much easier during the development phase. We wrote everything in Python 3.10 because all of the required computer vision and deep learning libraries have stable, well-tested builds for that version.

The system handles multiple video sources concurrently. Each camera runs inside its own background thread, managed by a dedicated \texttt{VideoProcessor} object. Memory and CPU usage were monitored throughout testing to catch any thread contention or resource leak issues early.


\section{Tools and Technologies Used}

\subsection*{Backend Web Framework: Flask + Flask-SocketIO}

Flask serves as the core web server. It handles all HTTP routes — authentication, camera configuration, metrics retrieval, and alert history. We chose it over heavier alternatives because it adds almost zero overhead to the response cycle and the routing model is transparent. Flask-SocketIO sits on top of Flask and manages the WebSocket connections that push live metric updates to the browser without needing the frontend to poll the server. Every time the AI engine finishes processing a frame, the resulting crowd metrics object is emitted directly to all subscribed clients on the relevant camera room. Alert delivery is near-instantaneous as a result.

\subsection*{Object Detection: Ultralytics YOLOv11s}

The actual detection model is YOLOv11 small (\texttt{yolo11s.pt}). We chose the small variant deliberately. The nano model was faster but produced too many false positives at lower confidence thresholds, which drove the people-count metric unreliably high. The small model gave better precision without the GPU memory demands of the medium or large variants. It runs inference at 960 pixels input resolution (\texttt{imgsz=960}) on CPU, which we validated as sufficient for video up to 1280px wide after automatic rescaling. We run detection with \texttt{classes=[0]}, restricting output to the person class only, and apply a minimum bounding box area filter of 400 square pixels to discard stray noise detections.

\subsection*{Multi-Object Tracking: BoT-SORT}

Detecting people frame-by-frame gives you a count. Tracking them gives you movement. We integrated BoT-SORT via the \texttt{tracker='botsort.yaml'} option built into Ultralytics. BoT-SORT combines a Kalman filter for motion prediction with appearance re-identification to recover track continuity when a person is briefly occluded. Each tracked individual gets a persistent \texttt{track\_id} across frames. We store up to 60 historical positions per ID in a dictionary-based \texttt{track\_history} structure. Stale tracks that have not produced a detection within three seconds are automatically pruned. The \texttt{lapx} library provides the linear assignment solver that BoT-SORT uses internally for matching.

\subsection*{Computer Vision: OpenCV}

OpenCV handles the low-level video work. It opens camera streams (\texttt{cv2.VideoCapture}) — accepting RTSP, HTTP, and local file paths interchangeably. It rescales oversized frames to 1280px wide before passing them to YOLO. It also drives the entire annotation pipeline: drawing the corner-style bounding boxes, velocity trail polylines, DBSCAN cluster convex hulls, flow direction arrows, proximity warning circles, and the semi-transparent HUD panel. All annotations are rendered in BGR colour space. The MJPEG stream delivered to the frontend is produced by encoding each annotated frame as JPEG at 80\% quality using \texttt{cv2.imencode}.

\subsection*{Database: SQLite via Flask-SQLAlchemy}

Metric records are written to a SQLite database through Flask-SQLAlchemy. A metric entry is saved once every 10 processed frames to avoid excessive write pressure on disk. The schema stores per-camera entries including crowd count, density, average velocity, surge rate, flow coherence, crowd pressure, risk score, risk level, and frame number. User credentials (hashed with bcrypt), camera configurations, alert records, and recording metadata are stored in separate tables. SQLite was sufficient for the expected data volume; moving to PostgreSQL only requires changing one environment variable.

\subsection*{Authentication and Security: PyJWT + bcrypt}

User sessions are managed with JSON Web Tokens signed using PyJWT. Passwords are hashed before storage with bcrypt. Three distinct user roles are enforced at the API level: Admin has full system control, Operator can start and stop camera feeds, and Viewer has read-only dashboard access. Role checks are applied as decorators on each API endpoint.

\subsection*{Alert Delivery: Telegram Bot API}

When risk thresholds are crossed, the \texttt{telegram\_service} module dispatches alert messages via the Telegram Bot API. The alert carries the camera name, the current risk level, crowd count, density, and a JPEG snapshot of the frame that triggered it. Alerts are rate-limited to prevent flooding during sustained high-density events.


\section{Methodologies and Algorithm Details}

The processing pipeline runs inside each \texttt{VideoProcessor} thread. Every frame goes through five stages in sequence: AI detection, ML behaviour analysis, risk scoring, annotation, and delivery. Below we describe the two most critical algorithmic components.

\subsection{Algorithm 1: Person Detection and BoT-SORT Tracking (\texttt{CrowdSafeAI.analyze\_frame})}

This is the entry point for all crowd intelligence. It receives a raw BGR video frame and returns a list of detections, each tagged with a stable tracking ID and a velocity estimate.

\begin{algorithm}[H]
\SetAlgoLined
\KwIn{BGR video frame $F$, area in square metres $A$, expected capacity $C$, frame rate $fps$}
\KwOut{Annotated frame, analysis dictionary}

Create a clean copy of $F$ before model inference to prevent in-place mutation by tracker\;
Run \texttt{model.track(F, tracker=botsort.yaml, classes=[0], persist=True)}\;
For each detected bounding box $(x_1, y_1, x_2, y_2)$ and track ID $t$:\;
\Indp
  Compute box area $= (x_2-x_1)(y_2-y_1)$; skip if $< 400$ px$^2$\;
  Compute aspect ratio; skip if $> 5.0$ (rejects horizontal noise)\;
  Compute centroid $c_x = (x_1+x_2)/2,\; c_y = (y_1+y_2)/2$\;
  Append $(c_x, c_y, t_{now})$ to \texttt{track\_history[t]}, keeping last 60 entries\;
  \eIf{$|$\texttt{track\_history[t]}$| \geq 2$}{
    Compute $dx, dy$ from previous to current centroid\;
    $v = \frac{\sqrt{dx^2 + dy^2} \times pixel\_to\_metre}{\Delta t}$ m/s\;
    Compute unit direction vector $(dx/|d|, dy/|d|)$\;
  }{
    $v \leftarrow 0.0$, direction $\leftarrow (0, 0)$\;
  }
\Indm
Prune stale track IDs not seen in the last 3 seconds\;
$N_{raw} \leftarrow$ number of passing detections\;
\eIf{$N_{raw} \geq dense\_crowd\_threshold$ (default 50)}{
  $N_{est} \leftarrow$ grid-based occlusion-corrected estimate using $occlusion\_factor = 1.3$\;
}{
  $N_{est} \leftarrow N_{raw}$\;
}
$\rho \leftarrow N_{est} / A$\;
$v_{avg} \leftarrow mean(velocities)$\;
Compute surge rate $S_r = std(v) / (mean(v) + \epsilon)$ when $mean(v) > 0.3$\;
Generate Gaussian-kernel density heatmap at $1/4$ resolution\;
\Return annotated frame, $\{N_{est}, \rho, v_{avg}, S_r, detections, density\_map, \ldots\}$\;

\caption{YOLOv11s + BoT-SORT Detection and Tracking}
\end{algorithm}

\vspace{0.4cm}

The surge rate metric deserves explanation. It measures the coefficient of variation in individual walking speeds — how unequally people within the crowd are moving. A completely calm crowd moves at roughly similar speeds, so the standard deviation stays low relative to the mean. When a disturbance starts and some people begin running while others stop or stand still, that ratio spikes. We threshold it at $mean(v) > 0.3$ m/s to avoid dividing near-zero values in stationary crowd situations.

\subsection{Algorithm 2: ML Behaviour Analysis and Risk Scoring}

Raw detections tell us where people are. The \texttt{CrowdAnalyzer} module tells us what the crowd is \textit{doing}. Six analyses run on each frame's detection set.

\subsubsection*{DBSCAN Spatial Clustering}

We group detected persons into spatial clusters using Density-Based Spatial Clustering of Applications with Noise (DBSCAN). The parameters are $\epsilon = 120$ pixels (neighbourhood radius) and $min\_samples = 2$. Persons closer than 120px to at least one other person are grouped; isolated individuals are labelled as noise (cluster $= -1$). Cluster centroids and sizes are returned for visualisation on the annotated frame as convex hull outlines.

\subsubsection*{Velocity Anomaly Detection via Z-Score}

Individual movement speeds that deviate significantly from the crowd average are flagged as anomalies. For each person, we compute:
$$z_i = \frac{v_i - \bar{v}}{\sigma_v}$$
Any $|z_i| > 2.0$ is marked as an anomaly. Fast movers ($z > 0$) signal running or panic behaviour. Stationary people in a moving crowd ($z < 0$) may indicate people who have fallen or are trapped. Both are worth surfacing to an operator.

\subsubsection*{Flow Coherence}

Flow coherence measures how uniformly the entire crowd is moving in the same direction:
$$coherence = \left| \frac{1}{n} \sum_{i=1}^{n} \hat{d}_i \right|$$
where $\hat{d}_i$ is the normalised direction unit vector for each tracked person, computed over a 10-frame sliding window. A coherence value near 1.0 means almost everyone is moving in the same direction — the signature of a stampede. A value near 0.0 is a normal crowd moving in random directions. Persons moving less than 2 pixels over the history window are excluded from this calculation.

\subsubsection*{Crowd Pressure}

Pressure combines local density (measured via mean nearest-neighbour distance) with velocity variance:
$$P = 0.6 \times P_{dist} + 0.4 \times P_{vel}$$
where $P_{dist} = \max(0,\; 1 - \bar{d}_{nn}/200)$ and $P_{vel} = \min(1,\; \sigma^2_v / 2)$. A crowd that is packed tightly and moving chaotically scores high on both components.

\subsubsection*{Risk Scoring (\texttt{RiskCalculator.calculate})}

The final risk score combines all signals through a weighted formula:

$$R = w_1 \cdot \rho_{norm} + w_2 \cdot S_{r,norm} + w_3 \cdot v^{-1}_{norm} + \Delta_P + \Delta_C$$

where:
\begin{itemize}
  \item $\rho_{norm} = \min(1,\; \rho / 10)$, normalised density (reference: 10 persons/m$^2$)
  \item $S_{r,norm} = \min(1,\; S_r / 2)$, normalised surge rate
  \item $v^{-1}_{norm}$: inverse velocity; stagnation below 0.2 m/s scores 1.0, normal movement above 1.5 m/s scores 0.0
  \item $\Delta_P = \max(0,\; P - 0.3) \times 0.15$, pressure boost
  \item $\Delta_C = \max(0,\; C_{flow} - 0.5) \times 0.2$, coherence boost for stampede-like movement
\end{itemize}

For crowds above 100 people, the base score is further multiplied by 1.15. The final score is clamped to $[0, 1]$ and mapped to four levels:

\begin{table}[!htbp]
\begin{center}
\def\arraystretch{1.3}
\resizebox{\textwidth}{!}{
\begin{tabular}{|c|c|c|}
\hline
\textbf{Risk Level} & \textbf{Score Range (\%)} & \textbf{Response} \\
\hline
SAFE & 0 -- 24 & No action \\
\hline
CAUTION & 25 -- 49 & Monitor closely \\
\hline
WARNING & 50 -- 74 & Alert operator \\
\hline
CRITICAL & 75 -- 100 & Immediate intervention \\
\hline
\end{tabular}
}
\end{center}
\caption{Risk classification thresholds}
\label{tab:risk-levels}
\end{table}

\subsubsection*{Temporal Trend Prediction via EMA}

The \texttt{CrowdAnalyzer} maintains a rolling deque of the last 60 density and risk score values. An Exponential Moving Average (EMA) with $\alpha = 0.3$ smooths the signal:
$$EMA_t = \alpha \cdot x_t + (1 - \alpha) \cdot EMA_{t-1}$$
If the current EMA exceeds the EMA computed 5 steps earlier by more than 0.1 for density or 0.03 for risk, the trend is classified as \textit{increasing} and shown on the HUD in red. A decreasing trend is shown in green. This gives operators an early heads-up that conditions are deteriorating before they cross a hard threshold.


\section{Verification and Validation for Acceptance}

We validated the system against three categories of test input.

\subsubsection*{Functional Validation: Detection Accuracy}

We ran the system on several publicly available crowd videos representing a range of densities — sparse (fewer than 20 persons visible), moderate (20--60 persons), and dense (60 or more). The YOLOv11s model produced reliable bounding boxes at the default \texttt{YOLO\_CONFIDENCE = 0.35} threshold. At this setting, the false positive rate was negligible on well-lit footage. In poorly lit test cases, lowering the minimum bounding box area filter to 300 px$^2$ helped. Track IDs remained stable across video sequences without significant identity switches on standard 30 fps footage.

\subsubsection*{Risk Score Validation: Threshold Calibration}

We built a small annotated test set by manually watching footage and labelling each segment as Safe, Caution, Warning, or Critical based on visual judgment. We then ran the same footage through the \texttt{RiskCalculator} and compared outputs. The formula agreed with manual labels in the vast majority of cases. The primary disagreement zone was the CAUTION-to-WARNING boundary, where moderate-density slow-moving crowds sometimes scored slightly lower than a human would rate them. We adjusted $w_3$ (velocity weight) upward to bring these cases into alignment.

\subsubsection*{Real-Time Performance Validation}

We measured end-to-end latency from camera frame capture to WebSocket emission of the resulting metrics object. On a standard laptop CPU (Intel Core i5, 8 GB RAM, no GPU), processing time per frame averaged under 200ms for video at 720p resolution with 20--30 detected persons. This is well within the target of one update per second. The MJPEG stream was delivered at 15 frames per second to the browser without buffering issues. Memory usage remained stable over 30-minute continuous processing sessions, confirming there are no meaningful reference leaks in the threading model.

\subsubsection*{Alert System Validation}

We confirmed that Telegram alerts fired correctly when risk level crossed WARNING or CRITICAL, and that the rate limiter correctly suppressed duplicate alerts during sustained elevated risk periods. The database metric write at every 10th frame was verified by querying the SQLite database after a session and checking that record counts matched expectations based on session duration and frame rate.
  
  
\chapter{Software Testing}

\section{Types of Testing Used}

We ran three layers of testing during development. Unit tests checked individual functions in isolation. Integration tests verified that the components talk to each other correctly. System tests ran the full pipeline end-to-end against real video footage. That last category was the most informative. It is where we caught the majority of our real bugs.

No automated test framework was used; the testing was done manually and systematically using crafted input conditions. Each test was documented with its input, the expected output from the source code logic, and what the system actually produced.


\section{Unit Testing}

Unit tests targeted the two most mathematically sensitive modules: \texttt{RiskCalculator} and \texttt{CrowdAnalyzer}.

\subsection*{Risk Calculator Tests}

The \texttt{RiskCalculator.calculate()} function takes six inputs and must return a score in $[0, 1]$ and one of four string labels. We tested it by constructing input scenarios that should land exactly at each classification boundary.

\begin{table}[!htbp]
\begin{center}
\def\arraystretch{1.35}
\resizebox{\textwidth}{!}{
\begin{tabular}{|c|p{3cm}|c|c|c|c|c|c|c|c|}
\hline
\textbf{TC\#} & \textbf{Scenario} & \textbf{Density} & \textbf{Velocity} & \textbf{Surge} & \textbf{Count} & \textbf{Pressure} & \textbf{Coherence} & \textbf{Expected} & \textbf{Result} \\
\hline
TC-01 & Empty area & 0.0 & 1.5 & 0.0 & 0 & 0.0 & 0.0 & SAFE ($\approx$0.00) & Pass \\
\hline
TC-02 & Normal walking crowd & 1.5 & 1.2 & 0.05 & 20 & 0.1 & 0.1 & SAFE ($\approx$0.17) & Pass \\
\hline
TC-03 & Moderate density, slow & 3.0 & 0.6 & 0.1 & 35 & 0.2 & 0.2 & CAUTION ($\approx$0.37) & Pass \\
\hline
TC-04 & High density, stagnant & 6.0 & 0.2 & 0.3 & 60 & 0.5 & 0.3 & WARNING ($\approx$0.59) & Pass \\
\hline
TC-05 & Surge event only & 1.0 & 1.0 & 1.5 & 30 & 0.1 & 0.1 & CAUTION ($\approx$0.34) & Pass \\
\hline
TC-06 & Large dense crowd ($>$100) & 7.0 & 0.3 & 0.5 & 120 & 0.7 & 0.7 & CRITICAL ($>$0.75) & Pass \\
\hline
TC-07 & Extreme density cap & 12.0 & 0.1 & 0.9 & 200 & 0.9 & 0.9 & CRITICAL (clamped 1.0) & Pass \\
\hline
TC-08 & Coherence boost triggers & 2.0 & 1.0 & 0.1 & 50 & 0.1 & 0.75 & WARNING boost applied & Pass \\
\hline
\end{tabular}
}
\end{center}
\caption{Risk Calculator Unit Test Cases}
\label{tab:tc-risk}
\end{table}

All eight cases passed. TC-07 specifically confirmed the $\min(0, 1)$ clamp works correctly; the score never exceeds 1.0 regardless of how extreme the inputs are.

\subsection*{Flow Coherence Tests}

We tested the \texttt{CrowdAnalyzer.\_flow\_analysis()} method with crafted track histories. Three scenarios were important to verify:

\begin{enumerate}
  \item All tracks moving in the same direction. Expected coherence $\approx 1.0$. Got 0.98. Pass.
  \item All tracks moving in uniformly random directions. Expected coherence $\approx 0.0$. Got 0.07. Pass.
  \item Fewer than 2 moving tracks (below 2px displacement threshold). Expected coherence $= 0.0$. Got 0.0. Pass.
\end{enumerate}

\subsection*{Velocity Anomaly Detection Tests}

We tested \texttt{\_detect\_anomalies()} with a velocity array where one person was moving at 3× the crowd's average speed. The z-score for that person exceeded 2.0 and the function returned it as a \texttt{fast\_mover} anomaly. We also tested a crowd smaller than 3 members, where the function is expected to return an empty list. Both passed.


\section{Integration Testing}

Integration tests checked that the modules interact without data loss or corruption when chained together.

\subsection*{Test: AI Engine to Crowd Analyzer Pipeline}

\begin{table}[!htbp]
\begin{center}
\def\arraystretch{1.35}
\resizebox{\textwidth}{!}{
\begin{tabular}{|c|p{4.5cm}|p{4.5cm}|c|}
\hline
\textbf{TC\#} & \textbf{Input Condition} & \textbf{Expected Behaviour} & \textbf{Result} \\
\hline
TC-09 & Single person in frame & DBSCAN returns 0 clusters (noise only), coherence = 0.0 & Pass \\
\hline
TC-10 & Two persons within 120px & DBSCAN returns 1 cluster of size 2 & Pass \\
\hline
TC-11 & Two persons beyond 120px & DBSCAN returns 0 clusters (both noise) & Pass \\
\hline
TC-12 & 5 persons, track IDs consistent across 3 frames & Velocity computed for each; track history accumulates & Pass \\
\hline
TC-13 & Track inactive for $>$3 seconds & Stale track pruned from history dict & Pass \\
\hline
\end{tabular}
}
\end{center}
\caption{AI Engine to Crowd Analyzer Integration Tests}
\label{tab:tc-integration}
\end{table}

\subsection*{Test: Alert Manager Trigger Logic}

The \texttt{AlertManager.check\_and\_alert()} function is the gatekeeper between analysis results and alert creation. We tested the four distinct trigger conditions coded in the source:

\begin{table}[!htbp]
\begin{center}
\def\arraystretch{1.35}
\resizebox{\textwidth}{!}{
\begin{tabular}{|c|p{4cm}|p{4cm}|p{3cm}|c|}
\hline
\textbf{TC\#} & \textbf{Metrics Input} & \textbf{Expected Trigger Type} & \textbf{Expected Alert} & \textbf{Result} \\
\hline
TC-14 & risk\_level=WARNING, density=7.0 & \texttt{extreme\_density} & WARNING fired & Pass \\
\hline
TC-15 & risk\_level=CRITICAL, surge\_rate=0.9 & \texttt{sudden\_surge} & CRITICAL fired & Pass \\
\hline
TC-16 & risk\_level=WARNING, velocity=0.1, density=5.0 & \texttt{stagnation\_with\_density} & WARNING fired & Pass \\
\hline
TC-17 & risk\_level=WARNING (no special condition) & \texttt{risk\_threshold} (fallback) & WARNING fired & Pass \\
\hline
TC-18 & risk\_level=SAFE & No alert & No alert & Pass \\
\hline
TC-19 & risk\_level=CAUTION & No alert & No alert & Pass \\
\hline
TC-20 & Second WARNING within 60s cooldown & Alert suppressed & No duplicate & Pass \\
\hline
\end{tabular}
}
\end{center}
\caption{Alert Manager Integration Test Cases}
\label{tab:tc-alert}
\end{table}

TC-20 is the most operationally important. In a sustained high-density situation, the system would fire continuously without the 60-second cooldown. The test confirmed that \texttt{\_last\_alert\_time} keyed on \texttt{camera\_id + risk\_level} correctly suppresses duplicates while still allowing a new CRITICAL to fire even if a WARNING fired 30 seconds earlier (different key).

\subsection*{Test: Metrics API Endpoints}

Each REST endpoint exposed by \texttt{metrics\_bp} was tested with a populated test database:

\begin{itemize}
  \item \texttt{GET /metrics/\{camera\_id\}} returned the correct JSON array, ordered chronologically, limited to the requested count.
  \item \texttt{GET /metrics/\{camera\_id\}/summary} returned correct aggregate statistics (\texttt{avg\_density}, \texttt{peak\_count}, \texttt{max\_risk\_score}) verified against the raw database records.
  \item \texttt{GET /metrics/\{camera\_id\}/aggregate?interval=hourly} grouped records correctly by the \texttt{\%Y-\%m-\%d \%H:00} SQLite strftime bucket.
  \item \texttt{GET /metrics/\{camera\_id\}/export?format=csv} returned a correctly structured CSV with all metric columns and a summary section.
\end{itemize}

All four endpoints returned HTTP 200 with correct data. Edge cases (empty camera, invalid camera ID) returned 404 or an empty JSON object as expected.


\section{System Testing}

System testing involved running the full application against real crowd video footage and observing end-to-end behaviour.

\subsection*{Test Scenario 1: Normal Pedestrian Flow}

A video of a shopping mall corridor with sparse foot traffic was processed. People walked freely at approximately 1.0--1.5 m/s. Expected: risk level stays SAFE throughout. Actual: risk score hovered between 0.10 and 0.22 across all frames. No alerts were generated. Dashboard updated in real time at approximately 10--15 fps MJPEG stream rate. Pass.

\subsection*{Test Scenario 2: Dense Crowd Entry Gate}

A video simulating a concert entry gate with a group of 25--30 people in a 3 m² area was processed. Density peaked at approximately 9 p/m², above the extreme\_density threshold of 6.0 p/m². Expected: CRITICAL alert within 10 seconds of crowd peaking. Actual: CRITICAL alert fired after the first frame where density crossed threshold. A second alert was correctly suppressed for the following 60 seconds. Telegram message arrived within 3 seconds of the alert being stored to the database. Pass.

\subsection*{Test Scenario 3: Stagnation Event}

A video of people suddenly stopping and bunching due to a simulated blockage was tested. Velocity dropped below 0.2 m/s while density climbed above 4.0 p/m²---exactly the \texttt{stagnation\_with\_density} trigger condition. Alert was generated with correct trigger type string. Pass.

\subsection*{Test Scenario 4: Multiple Camera Streams}

Two separate \texttt{VideoProcessor} threads were started simultaneously. Each processed its own video independently. SocketIO correctly emitted metrics to camera-specific rooms (\texttt{camera\_\{id\}}) so that metrics from one camera did not appear on the dashboard of the other. Database writes from both threads did not produce race conditions or duplicate primary key errors over a 10-minute test. Pass.

\begin{table}[!htbp]
\begin{center}
\def\arraystretch{1.35}
\resizebox{\textwidth}{!}{
\begin{tabular}{|c|p{4cm}|c|c|c|}
\hline
\textbf{Test} & \textbf{Scenario} & \textbf{Risk Level} & \textbf{Alert Fired} & \textbf{Result} \\
\hline
ST-01 & Normal pedestrian flow & SAFE & No & Pass \\
\hline
ST-02 & Dense entry gate (9 p/m²) & CRITICAL & Yes (within 60s cooldown) & Pass \\
\hline
ST-03 & Stagnation with density & WARNING & Yes (stagnation trigger) & Pass \\
\hline
ST-04 & Two concurrent cameras & Varies & Per camera & Pass \\
\hline
ST-05 & Video upload (.mp4) & Varies & Correct & Pass \\
\hline
ST-06 & Invalid RTSP stream URL & System error state & No crash & Pass \\
\hline
\end{tabular}
}
\end{center}
\caption{System-Level Test Results Summary}
\label{tab:tc-system}
\end{table}

ST-06 verified the error handling path. When an invalid source URL is given, \texttt{cv2.VideoCapture.isOpened()} returns false, the processor sets status to \texttt{error} in the database, emits a \texttt{camera\_status} event via SocketIO, and exits cleanly. No crash, no hanging thread.


\chapter{Results}

\section{System Output Description}

The annotated video stream carries six layers of information rendered directly on the frame. Each detected person gets a corner-style bounding box. The box colour changes based on walking speed: green for slow movement, amber for moderate, orange for fast-moving individuals, and purple for anyone whose velocity z-score exceeds 2.0 (anomalous). A fading trail of up to 15 historical positions shows recent movement direction. Persons grouped within 120 pixels of each other by DBSCAN are surrounded by a convex hull outline labelled with a group number and member count. Flow direction arrows indicate the averaged movement vector for each track. Proximity warning circles appear between pairs of persons who are within 80 pixels of each other. The semi-transparent HUD panel in the top-left corner shows live crowd count, number of clusters, flow coherence (0 to 1), and crowd pressure score. The risk badge in the top-right corner shows the current level in its corresponding colour. A 180$\times$70 pixel sparkline chart below it plots density and risk score history over the last 60 frames.

\section{System Screenshots}

The following figures illustrate the primary user interfaces and monitoring outputs of the CrowdSafe system.

\begin{figure}[H]
    \centering
    \includegraphics[width=0.9\textwidth]{dashboard_main.png}
    \caption{Main Operator Dashboard showing live video feed with AI annotations, HUD stats, and real-time risk level badge.}
    \label{fig:dashboard}
\end{figure}

\begin{figure}[H]
    \centering
    \includegraphics[width=0.8\textwidth]{alerts_log.png}
    \caption{Alerts History interface showing recorded incidents with trigger conditions and metric snapshots.}
    \label{fig:alerts}
\end{figure}

\begin{figure}[H]
    \centering
    \includegraphics[width=0.8\textwidth]{metrics_charts.png}
    \caption{Analytics Dashboard displaying historical trends for density, velocity, and risk scores across multiple sessions.}
    \label{fig:metrics}
\end{figure}

\begin{figure}[H]
    \centering
    \includegraphics[width=0.8\textwidth]{telegram_alert.png}
    \caption{Telegram mobile notification showing a CRITICAL incident alert with a frame snapshot.}
    \label{fig:telegram}
\end{figure}

\begin{figure}[H]
    \centering
    \includegraphics[width=0.8\textwidth]{heatmap_view.png}
    \caption{Crowd density heatmap overlay mode, visualizing high-risk accumulation zones.}
    \label{fig:heatmap}
\end{figure}


\section{Observed Performance Metrics}

\begin{table}[!htbp]
\begin{center}
\def\arraystretch{1.35}
\resizebox{\textwidth}{!}{
\begin{tabular}{|l|c|c|}
\hline
\textbf{Metric} & \textbf{Observed Value} & \textbf{Test Condition} \\
\hline
Average frame processing time & $<$200 ms/frame & 720p video, 20--30 persons, CPU only \\
\hline
MJPEG stream frame rate & 15 fps & Browser dashboard, single camera \\
\hline
WebSocket metrics emit delay & $<$50 ms & Local network, Flask-SocketIO \\
\hline
Telegram alert delivery delay & 2--4 seconds & Stable internet connection \\
\hline
DB metric record interval & Every 10 frames & SQLite, no write errors \\
\hline
Memory usage (30 min session) & Stable (no growth) & Single camera, 720p \\
\hline
YOLOv11s detection confidence threshold & 0.35 & Default config setting \\
\hline
Track ID stability (30 fps footage) & No significant switches & 30-person test clip \\
\hline
\end{tabular}
}
\end{center}
\caption{Observed System Performance Metrics}
\label{tab:perf}
\end{table}


\section{Risk Threshold Calibration Results}

The risk formula thresholds were calibrated against crowd science literature. Based on research by Prof. Keith Still (University of Suffolk) on crowd safety density benchmarks, the following real-world reference table shows how CrowdSafe's output levels align with physical crowd conditions:

\begin{table}[!htbp]
\begin{center}
\def\arraystretch{1.35}
\resizebox{\textwidth}{!}{
\begin{tabular}{|c|l|l|c|}
\hline
\textbf{Density (p/m²)} & \textbf{Physical Condition} & \textbf{Experience} & \textbf{CrowdSafe Level} \\
\hline
$< 0.5$ & Free movement & Full freedom of movement & SAFE \\
\hline
$0.5$ -- $1.0$ & Comfortable & Normal walking, path choice & SAFE \\
\hline
$1.0$ -- $2.0$ & Restricted & Reduced speed & SAFE \\
\hline
$2.0$ -- $3.5$ & Crowded & Shoulder-to-shoulder & CAUTION \\
\hline
$3.5$ -- $5.0$ & Very crowded & Involuntary contact, shuffling & CAUTION--WARNING \\
\hline
$5.0$ -- $6.0$ & Dangerous & No voluntary movement & WARNING \\
\hline
$6.0$ -- $7.0$ & \textbf{Critical} & Breathing restricted, crush force begins & \textbf{WARNING--CRITICAL} \\
\hline
$7.0$ -- $9.0$ & \textbf{Lethal zone} & Compressive asphyxia possible & \textbf{CRITICAL} \\
\hline
$> 9.0$ & \textbf{Fatal} & Stampede / crush fatalities likely & \textbf{CRITICAL} \\
\hline
\end{tabular}
}
\end{center}
\caption{Real-world crowd density reference vs.~CrowdSafe risk levels (based on crowd safety research)}
\label{tab:density-ref}
\end{table}

The system's WARNING trigger at density $> 6.0$ p/m² aligns with the physical onset of crush force. CRITICAL fires when the model score exceeds 0.75, which requires either sustained extreme density or a combination of moderate density with stagnation and high flow coherence.


\section{Risk Score Simulation Results}

The following table shows predicted risk scores at varying crowd densities, assuming moderate velocity (0.5 m/s) and low surge (0.1). These values were produced by evaluating the full formula from \texttt{RiskCalculator.calculate()}:

\begin{table}[!htbp]
\begin{center}
\def\arraystretch{1.35}
\resizebox{\textwidth}{!}{
\begin{tabular}{|c|c|c|c|c|c|}
\hline
\textbf{People} & \textbf{Area (m²)} & \textbf{Density (p/m²)} & \textbf{Risk Score} & \textbf{Level} & \textbf{Alert} \\
\hline
5 & 5 & 1.00 & 0.29 & CAUTION & No \\
\hline
15 & 5 & 3.00 & 0.37 & CAUTION & No \\
\hline
20 & 5 & 4.00 & 0.41 & CAUTION & No \\
\hline
25 & 5 & 5.00 & 0.45 & CAUTION & No \\
\hline
15 & 2 & 7.50 & 0.58 & WARNING & Yes \\
\hline
20 & 2 & 10.0 (cap) & 0.65 & WARNING & Yes \\
\hline
25 & 2 & 12.5 (cap at 10) & 0.75 & CRITICAL & Yes \\
\hline
120 & 10 & 12.0 (cap, $>$100) & $\geq$0.75 & CRITICAL & Yes \\
\hline
\end{tabular}
}
\end{center}
\caption{Risk score simulation results (moderate velocity=0.5 m/s, surge=0.1, no ML boosts)}
\label{tab:risk-sim}
\end{table}

The density normalisation cap at 10 p/m² means the base score from density alone plateaus at 0.40 (its 40\% weight). A score above 0.75 into CRITICAL territory requires the velocity and surge components to also contribute, or the ML boosts from crowd pressure and flow coherence to activate. This is intentional: no single signal should single-handedly push the system into CRITICAL. Three independent signals must collectively agree the situation is dangerous.


\section{Export and Reporting Output}

The system exports session data in four formats, all served through the \texttt{/api/metrics/\{camera\_id\}/export} endpoint:

\begin{itemize}
  \item \textbf{CSV} --- flat file with one row per stored metric record. Fields include timestamp, count, density, avg\_velocity, surge\_rate, risk\_score, risk\_level, flow\_coherence, and crowd\_pressure. A summary block at the top shows avg\_density, peak\_count, avg\_count, and max\_risk\_score for the session.
  \item \textbf{DOCX} --- Word document with the summary statistics in a formatted table, followed by the full metric time series.
  \item \textbf{PDF} --- same content as DOCX, rendered to PDF using \texttt{fpdf2}.
  \item \textbf{Markdown} --- human-readable report suitable for version control or quick sharing.
\end{itemize}

All four format outputs were verified in system testing. CSV files opened correctly in spreadsheet software without encoding issues. PDF output was rendered correctly by standard viewers.
\chapter{Deployment and Maintenance}

\section{Installation and Uninstallation}

CrowdSafe runs as a Python web application and has no installer wizard. The setup process is manual but straightforward. You need Python 3.10 or later on the host machine. On Windows, WSL2 with Ubuntu is the most reliable environment; on Linux, a native install is fine.

\subsubsection*{Step 1 — Clone the Repository}

Obtain the source code by cloning the project repository into a directory of your choice:

\begin{verbatim}
git clone <repository-url> CrowdSafe
cd CrowdSafe
\end{verbatim}

\subsubsection*{Step 2 — Create and Activate a Virtual Environment}

Create an isolated Python environment so that the project dependencies do not conflict with anything else on the machine:

\begin{verbatim}
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Linux / macOS
\end{verbatim}

\subsubsection*{Step 3 — Install Dependencies}

All required packages are listed in \texttt{requirements.txt}. Install them with:

\begin{verbatim}
pip install -r requirements.txt
\end{verbatim}

The main dependencies are Flask 3.1, Flask-SocketIO 5.5, Flask-SQLAlchemy 3.1, Ultralytics 8.3 (which downloads the YOLOv11 weights on first run), OpenCV 4.10 (headless build), NumPy 2.2, PyJWT 2.10, and bcrypt 4.2. On first startup, Ultralytics will automatically download \texttt{yolo11s.pt} from the Ultralytics CDN if the model file is not already present in the configured model folder.

\subsubsection*{Step 4 — Configure Environment Variables}

Copy the supplied example configuration file:

\begin{verbatim}
cp .env.example .env
\end{verbatim}

Open \texttt{.env} in a text editor and set the following values:

\begin{itemize}
  \item \texttt{SECRET\_KEY}: a long random string used to sign JWT tokens
  \item \texttt{DATABASE\_URL}: the SQLite or PostgreSQL connection string
  \item \texttt{TELEGRAM\_BOT\_TOKEN} and \texttt{TELEGRAM\_CHAT\_ID}: required if alert delivery via Telegram is needed
  \item \texttt{YOLO\_MODEL}: model filename inside the models folder (default \texttt{yolo11s.pt})
  \item \texttt{YOLO\_CONFIDENCE}: detection confidence threshold (default 0.35)
\end{itemize}

\subsubsection*{Step 5 — Initialise the Database}

The database tables are created on first application startup via SQLAlchemy's \texttt{create\_all} call inside the application factory. No separate migration command is needed for a fresh install. The default admin account is created automatically with credentials specified in the environment file.

\subsubsection*{Step 6 — Start the Application}

Run the development server with:

\begin{verbatim}
python app.py
\end{verbatim}

For production deployment, the system is containerised using the included \texttt{Dockerfile} and \texttt{docker-compose.yml}. The Docker setup places Gunicorn (configured for SocketIO's async mode) behind an Nginx reverse proxy. Start it with:

\begin{verbatim}
docker-compose up --build
\end{verbatim}

The application then listens on port 80 via Nginx. Gunicorn is configured with the \texttt{geventwebsocket} worker to handle WebSocket connections correctly.

\subsubsection*{Uninstallation}

To remove the application from the system, stop any running server or container, delete the project directory, remove the virtual environment folder (if not inside the project directory), and optionally drop the database file or schema. There are no registry entries or system services created by the application itself.


\section{User Help}

\subsubsection*{Logging In}

Open the application URL in a browser. The login page asks for a username and password. Three roles exist: Admin, Operator, and Viewer. Admins see all configuration controls. Operators can start and stop camera feeds. Viewers get a read-only dashboard. If you forget credentials, an Admin account can reset other users' passwords from the user management panel.

\subsubsection*{Adding a Camera}

Go to the Cameras section in the navigation menu. Click Add Camera. Provide a name, the video source URL (supports RTSP streams, HTTP-based IP camera feeds, and local file paths for testing), the physical area in square metres that the camera covers, and the expected maximum capacity. These last two values feed directly into the density and risk calculations, so they should reflect real measurements of the monitored space. Click Save.

\subsubsection*{Starting and Stopping Monitoring}

Select a camera from the camera list. Click Start Processing. The backend spawns a background thread that captures frames, runs detection and tracking, computes crowd metrics every frame, saves a metric record to the database every 10 frames, and streams the annotated MJPEG video back to the dashboard. The dashboard updates in real time via WebSocket — there is no need to refresh the page. Crowd count, density, risk level, flow coherence, and crowd pressure are all shown live. Click Stop Processing to end the session. The system automatically saves the annotated session recording as an MP4 file.

\subsubsection*{Reading the Dashboard}

The live video panel overlays the following information directly on the frame:
\begin{itemize}
  \item Corner-style bounding boxes around each detected person, colour-coded by movement speed (green for slow, amber for moderate, orange for fast, purple for anomalous)
  \item Cluster outlines drawn as convex hulls around spatial groups, labelled with group number and member count
  \item Flow direction arrows showing each tracked person's recent movement vector
  \item A heads-up display panel (top-left) showing live people count, cluster count, flow coherence value, and crowd pressure score
  \item A risk badge (top-right) in green, amber, orange, or red matching the current SAFE / CAUTION / WARNING / CRITICAL classification
  \item A sparkline chart showing density and risk score history over the last 60 frames
\end{itemize}

\subsubsection*{Viewing Alerts and Historical Data}

All generated alerts appear in the Alerts section with timestamp, camera source, risk level at trigger, and the crowd metrics recorded at that moment. The Metrics section provides historical charts for all stored sessions. Recordings saved as MP4 files are accessible through the Recordings section and can be downloaded directly from the interface.

\subsubsection*{Troubleshooting}

If a camera feed does not start, verify that the source URL is reachable from the server machine. RTSP streams often require the correct port to be open on the network. If the model fails to load on startup, confirm that the \texttt{yolo11s.pt} file is present in the configured models folder or that the machine has internet access so Ultralytics can download it automatically. If Telegram alerts are not arriving, check that the bot token and chat ID in \texttt{.env} are correct and that the bot has been started by the target user in Telegram.
     
 \chapter{Conclusion and future scope}

\begin{itemize}
    \item Conclusion:
\end{itemize}

The CrowdSafe system implementation shows how artificial intelligence solutions can improve public safety and help manage crowd control operations. The system uses computer vision and deep learning together with real-time data processing to achieve precise identification of people and research their crowd distribution and movement patterns throughout changing environments. The system achieves its goals through two main advantages which allow it to maintain constant surveillance while people work at their tasks.\\

The system provides timely alerts and actionable insights through its evaluation of crowd conditions which uses multiple parameters including density and velocity and flow direction. This helps authorities take proactive measures to prevent dangerous situations like stampedes, overcrowding, and congestion. The system's modular architecture allows it to scale and adapt to different environments which include railway stations and events and public gatherings.\\

The project successfully achieves its goal to build a dependable system which efficiently monitors crowds while providing intelligent support for decision-making in actual situations.\\

\vspace{3 cm}
\begin{itemize}
    \item Futute Scope:
\end{itemize}

The CrowdSafe system requires advanced predictive analytics and AI models which need to forecast crowd behavior based on historical data and real-time trends. The system will enable early warning systems which prevent incidents before risk conditions reach their full development stage.\\

The system supports large-scale deployment across smart city infrastructures which connect multiple camera networks to a central monitoring system. The system analysis improves through IoT device integration which includes temperature sensors and sound sensors and pressure sensors to provide additional contextual data.\\

Organizations can implement edge computing techniques which enable data processing to occur near its source while achieving better real-time performance through reduced latency. The system achieves better scalability through cloud integration which also improves storage capacity and remote system accessibility.\\

The system will gain better security and surveillance features through the addition of facial recognition technology and identity tracking capabilities and anomaly detection systems. The development of a mobile application interface will enable users to receive instant alerts while they monitor information through their handheld devices.\\

The system will achieve better performance through ongoing improvements in model accuracy and optimization methods and environmental condition adaptability. The system development process will create more affordable systems which require less effort to deploy in different fields of application.\\

% \bibliographystyle{plain}

\bibliographystyle{ieeetr}
\bibliography{reference.bib}
\begin{enumerate}
    \item H. H. Y. Sa’ad, Y. Al-Ashmoery, A. Haider, A. Zaid, K. Alwasbi, and R. H. Salman, “Crowd detection, monitoring and management: A literature review,” Journal of Amran University, vol. 3, pp. 259–261, 2023. ([ResearchGate][1])\\
     
    \item P. Kannan, V. Jadhav, Y. Patil, K. Hyalij, and P. Bacchav, “Real-time crowd monitoring and management,” International Research Journal on Advanced Engineering Hub, vol. 3, no. 3, pp. 949–953, 2025. ([ResearchGate]\\
    
    \item A. A. Khan et al., “Crowd anomaly detection in video frames using fine-tuned AlexNet,” Electronics, vol. 11, no. 19, pp. 3105, 2022. ([MDPI][3])\\
     
    \item J. Liu, C. Gao, D. Meng, and A. G. Hauptmann, “DecideNet: Counting varying density crowds through attention guided detection and density estimation,” in Proc. IEEE Conf. Computer Vision, 2017.\\
     
    \item S. Shao, Z. Zhao, B. Li, T. Xiao, G. Yu, X. Zhang, and J. Sun, “CrowdHuman: A benchmark for detecting human in a crowd,” in Proc. IEEE Conf. Computer Vision and Pattern Recognition, 2018.\\
     
    \item K. Singh, S. Rajora, D. K. Vishwakarma, G. Tripathi, S. Kumar, and G. S. Walia, “Crowd anomaly detection using aggregation of ensembles of fine-tuned ConvNets,” Neurocomputing, vol. 371, pp. 188–198, 2019.\\
     
    \item A. Ramchandran and A. K. Sangaiah, “Unsupervised deep learning system for local anomaly event detection in crowded scenes,” Multimedia Tools and Applications, vol. 79, pp. 35275–35295, 2019.\\
     
    \item A. Bamaqa, M. Sedky, T. Bosakowski, B. B. Bastaki, and N. O. Alshammari, “SIMCD: Simulated crowd data for anomaly detection and prediction,” Expert Systems with Applications, vol. 203, pp. 117475, 2022.\\
     
    \item M. U. K. Khan, H. S. Park, and C. M. Kyung, “Rejecting motion outliers for efficient crowd anomaly detection,” IEEE Transactions on Information Forensics and Security, vol. 14, pp. 541–556, 2018.\\
     
    \item A. Mohan and D. Choksi, “Crowd anomaly detection using PCA and CNN,” in Proc. Int. Conf. Intelligent Systems, 2020.\\
     
\end{enumerate}
\begin{appendices}

\chapter{References}
(Strictly in ACM Format)

% \chapter{ALGORITHMIC DESIGN}
\chapter{Laboratory assignments on Project Analysis of Algorithmic Design}
\begin{itemize}
\item To develop the problem under consideration and justify feasibilty using
concepts of knowledge canvas and IDEA Matrix.\\
Refer \cite{innovationbook} for IDEA Matrix and Knowledge canvas model. Case studies are given in this book. IDEA Matrix is represented in the following form. Knowledge canvas represents about identification  of opportunity for product. Feasibility is represented w.r.t. business perspective.\\ 

\begin{table}[!htbp]
\begin{center}
  \begin{tabular}{| c | c | c | c |}
\hline
 I & D & E & A \\ 
\hline
Increase & Drive & Educate & Accelerate \\
\hline
Improve & Deliver & Evaluate & Associate  \\
 \hline
Ignore & Decrease & Eliminate & Avoid \\
\hline
\end{tabular}
 \caption { IDEA Matrix }
 \label{tab:imatrix}
\end{center}
\end{table}

\item Project problem statement feasibility assessment using NP-Hard, NP-Complete or satisfy ability issues using modern algebra and/or relevant mathematical models.
\item input x,output y, y=f(x)
\end{itemize}

\chapter{Laboratory assignments on Project Quality and Reliability Testing of Project Design}

It should include assignments such as
\begin{itemize}
\item Use of divide and conquer strategies to exploit distributed/parallel/concurrent processing of the above to identify object, morphisms, overloading in functions (if any), and functional relations and any other dependencies (as per requirements).
             It can include Venn diagram, state diagram, function relations, i/o relations; use this to derive objects, morphism, overloading

\item Use of above to draw functional dependency graphs and relevant Software modeling methods, techniques
including UML diagrams or other necessities using appropriate tools.
\item Testing of project problem statement using generated test data (using mathematical models, GUI, Function testing principles, if any) selection and appropriate use of testing tools, testing of UML diagram's reliability. Write also test cases [Black box testing] for each identified functions. 
You can use Mathematica or equivalent open source tool for generating test data. 
\item Additional assignments by the guide. If project type as Entreprenaur, Refer \cite{ehr},\cite{mckinsey},\cite{mckinseyweb}, \cite{govwebsite}
\end{itemize}


\chapter{Project Planner}
\label{app:plan}
Using planner or alike project management tool.




\chapter{Published Papers}

\begin{enumerate}
\item Paper Title:
\item Name of the Conference/Journal where paper Published :
\item Google Scholar/Scopus: 
  

\end{enumerate}

\chapter{Plagiarism Report}
Plagiarism report
\chapter{ Term-II Project Laboratory Assignments}
\begin{enumerate}
\item Review of design and necessary corrective actions taking into consideration the feedback report of Term I assessment, and other competitions/conferences participated like IIT, Central Universities, University Conferences or equivalent centers of excellence etc.
\item Project workstation selection, installations along with setup and installation report preparations.
\item Programming of the project functions, interfaces and GUI (if any) as per 1 st Term term-work submission using corrective actions recommended in Term-I assessment of Term-work.
\item Test tool selection and testing of various test cases for the project performed and generate various testing result charts, graphs etc. including reliability testing.\\
\textbf{Additional assignments for the Entrepreneurship Project:}
\item Installations and Reliability Testing Reports at the client end.

\end{enumerate}
\chapter{Information of Project Group Members}
one page for each student .
\newpage
\begin{enumerate}
\item Name :   \hspace{90 mm}\includegraphics[width=60pt]{photo.jpg}
\item Date of Birth : 
\item Gender : Male
\item Permanent Address :
\item E-Mail : 
\item Mobile/Contact No. :
\item Placement Details :
\item Paper Published : 

\end{enumerate}
\end{appendices}


\end{document}
