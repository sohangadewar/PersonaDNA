
# ============================================================
# PersonaDNA - Jarvis Voice Recruiter Assistant
# ============================================================

import speech_recognition as sr
import pyttsx3


# ============================================================
# Text-to-Speech
# ============================================================

engine = pyttsx3.init()

engine.setProperty("rate", 165)
engine.setProperty("volume", 1.0)


def speak(text: str):
    """Print and speak Jarvis response."""

    print(f"\nJarvis: {text}")

    try:
        engine.say(text)
        engine.runAndWait()
    except Exception as error:
        print(f"TTS Error: {error}")


# ============================================================
# Speech Recognition
# ============================================================

recognizer = sr.Recognizer()


def listen():
    """Listen to microphone and convert speech to text."""

    try:
        with sr.Microphone() as source:

            print("\nListening...")

            recognizer.adjust_for_ambient_noise(
                source,
                duration=0.5
            )

            try:
                audio = recognizer.listen(
                    source,
                    timeout=5,
                    phrase_time_limit=10
                )

            except sr.WaitTimeoutError:
                print("No speech detected.")
                return ""

    except OSError as error:
        print(f"Microphone Error: {error}")
        speak("I cannot access the microphone.")
        return ""

    try:

        print("Processing speech...")

        command = recognizer.recognize_google(audio)

        print(f"You: {command}")

        return command.lower().strip()

    except sr.UnknownValueError:

        print("Sorry, I could not understand that.")

        speak(
            "Sorry, I could not understand what you said."
        )

        return ""

    except sr.RequestError as error:

        print(
            f"Speech recognition service error: {error}"
        )

        speak(
            "I am unable to connect to the speech recognition service."
        )

        return ""


# ============================================================
# PersonaDNA Command Processor
# ============================================================

def process_jarvis_command(
    command: str,
    analysis_result: dict,
):

    command = command.lower().strip()

    # --------------------------------------------------------
    # Introduction
    # --------------------------------------------------------

    if (
        "introduce yourself" in command
        or "who are you" in command
        or "what are you" in command
        or "tell me about yourself" in command
    ):

        return (
            "I am Jarvis, the AI recruiting assistant "
            "of PersonaDNA. I analyze candidate evidence "
            "from resumes, GitHub, and LinkedIn, and help "
            "recruiters understand candidate trust, skills, "
            "risks, and verification."
        )

    # --------------------------------------------------------
    # Purpose
    # --------------------------------------------------------

    if (
        "your purpose" in command
        or "what is your purpose" in command
        or "what do you do" in command
        or "purpose of personadna" in command
    ):

        return (
            "My purpose is to help recruiters verify "
            "candidate claims using real evidence. "
            "I can report the candidate's trust score, "
            "AI confidence, verified claims, risk level, "
            "recruiter verdict, skills, and projects."
        )

    # --------------------------------------------------------
    # Trust Score
    # --------------------------------------------------------

    if (
        "trust score" in command
        or "trust level" in command
        or "how trustworthy" in command
    ):

        return (
            f"The candidate trust score is "
            f"{analysis_result.get('trust_score', 0)}."
        )

    # --------------------------------------------------------
    # AI Confidence
    # --------------------------------------------------------

    if (
        "ai confidence" in command
        or "confidence score" in command
        or "confidence" in command
    ):

        return (
            f"The AI confidence is "
            f"{analysis_result.get('ai_confidence', 0)} percent."
        )

    # --------------------------------------------------------
    # Verified Claims
    # --------------------------------------------------------

    if (
        "verified claims" in command
        or "verified claim" in command
        or "how many claims" in command
    ):

        return (
            f"There are "
            f"{analysis_result.get('verified_claims', 0)} "
            f"verified claims."
        )

    # --------------------------------------------------------
    # Risk
    # --------------------------------------------------------

    if (
        "risk level" in command
        or "candidate risk" in command
        or command == "risk"
        or "what is the risk" in command
    ):

        return (
            f"The current risk level is "
            f"{analysis_result.get('risk_level', 'unknown')}."
        )

    # --------------------------------------------------------
    # Recruiter Verdict
    # --------------------------------------------------------

    if (
        "recruiter verdict" in command
        or "candidate verdict" in command
        or "verdict" in command
        or "should i hire" in command
    ):

        return (
            f"The recruiter verdict is "
            f"{analysis_result.get('recruiter_verdict', 'unknown')}."
        )

    # --------------------------------------------------------
    # Skills
    # --------------------------------------------------------

    if (
        "candidate skills" in command
        or "what skills" in command
        or "skills" in command
        or "technical skills" in command
    ):

        skills = analysis_result.get(
            "skills",
            []
        )

        if not skills:

            return (
                "No candidate skills are currently "
                "available in the analysis."
            )

        return (
            "The candidate skills are "
            + ", ".join(skills)
            + "."
        )

    # --------------------------------------------------------
    # Projects
    # --------------------------------------------------------

    if (
        "projects" in command
        or "candidate projects" in command
        or "what projects" in command
    ):

        projects = analysis_result.get(
            "projects",
            []
        )

        if not projects:

            return (
                "I do not have project information "
                "available in the current analysis."
            )

        return (
            "The candidate has the following projects: "
            + ", ".join(projects)
            + "."
        )

    # --------------------------------------------------------
    # Help
    # --------------------------------------------------------

    if (
        "help" in command
        or "what can you do" in command
        or "commands" in command
    ):

        return (
            "You can ask me to introduce myself, "
            "explain my purpose, provide the trust score, "
            "AI confidence, verified claims, risk level, "
            "recruiter verdict, candidate skills, "
            "or candidate projects."
        )

    # --------------------------------------------------------
    # Exit
    # --------------------------------------------------------

    if (
        command == "exit"
        or command == "quit"
        or command == "stop"
        or command == "goodbye"
        or "shut down" in command
    ):

        return "__EXIT__"

    # --------------------------------------------------------
    # Unknown Command
    # --------------------------------------------------------

    return (
        "I could not find that information in the "
        "candidate analysis. You can ask about the "
        "trust score, AI confidence, verified claims, "
        "risk level, recruiter verdict, skills, "
        "or projects."
    )


# ============================================================
# Start Jarvis
# ============================================================

def start_jarvis(analysis_result=None):

    # --------------------------------------------------------
    # Temporary test data
    # --------------------------------------------------------

    if analysis_result is None:

        analysis_result = {

            "trust_score": 74,

            "ai_confidence": 78,

            "verified_claims": 6,

            "risk_level": "Medium",

            "recruiter_verdict": (
                "Consider for Technical Interview "
                "after further verification"
            ),

            "skills": [
                "Python",
                "Java",
                "JavaScript",
                "React",
                "HTML",
                "CSS",
                "FastAPI",
                "Flask",
                "REST",
                "SQL",
                "PostgreSQL",
                "Artificial Intelligence",
                "Machine Learning",
                "Data Science",
                "Git",
                "GitHub",
                "Google Cloud",
                "RAG",
                "LangChain",
            ],

            "projects": [
                "PersonaDNA",
                "Smart Attendance System",
                "PlacementGPT",
                "Jarvis AI Desktop Assistant",
            ],
        }

    # --------------------------------------------------------
    # Startup
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("PERSONADNA JARVIS")
    print("=" * 60)

    speak(
        "Hello. I am Jarvis, the PersonaDNA AI recruiting assistant."
    )

    speak(
        "I am ready to answer questions about the candidate."
    )

    # --------------------------------------------------------
    # Main Voice Loop
    # --------------------------------------------------------

    while True:

        command = listen()

        if not command:
            continue

        response = process_jarvis_command(
            command,
            analysis_result
        )

        if response == "__EXIT__":

            speak(
                "Goodbye. PersonaDNA verification session ended."
            )

            break

        speak(response)


# ============================================================
# Run Directly
# ============================================================

if __name__ == "__main__":

    start_jarvis()
