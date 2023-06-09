import random
import time
import os

import speech_recognition as sr # speech recognition
import openai                   # gpt
import pyttsx3                  # For text to speech

PROMPT_LIMIT = 50 # Don't set this too high.
MAX_WORDS = 400
TIME_OUT_TIME = 5 # In seconds
ENERGY_THRESHOLD = 400
openai.api_key = os.getenv("OPENAI_API_KEY")
assert(openai.api_key is not None)

def recognize_speech_from_mic(recognizer, microphone):
    """Transcribe speech from recorded from `microphone`.

    Returns a dictionary with three keys:
    "success": a boolean indicating whether or not the API request was
               successful
    "error":   `None` if no error occured, otherwise a string containing
               an error message if the API could not be reached or
               speech was unrecognizable
    "transcription": `None` if speech could not be transcribed,
               otherwise a string containing the transcribed text
    """
    # check that recognizer and microphone arguments are appropriate type
    if not isinstance(recognizer, sr.Recognizer):
        raise TypeError("`recognizer` must be `Recognizer` instance")

    if not isinstance(microphone, sr.Microphone):
        raise TypeError("`microphone` must be `Microphone` instance")

    # adjust the recognizer sensitivity to ambient noise and record audio
    # from the microphone
    with microphone as source:
        print("Shell says: Start talking!\n\n")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source, timeout=TIME_OUT_TIME)

    # set up the response object
    response = {
        "success": True,
        "error": None,
        "transcription": None
    }

    # try recognizing the speech in the recording
    # if a RequestError or UnknownValueError exception is caught,
    #     update the response object accordingly
    try:
        response["transcription"] = recognizer.recognize_google(audio)
    except sr.RequestError:
        # API was unreachable or unresponsive
        response["success"] = False
        response["error"] = "API unavailable"
    except sr.UnknownValueError:
        # speech was unintelligible
        response["error"] = "Unable to recognize speech"

    return response


if __name__ == "__main__":

    # create recognizer and mic instances
    recognizer = sr.Recognizer()
    recognizer.dynamic_energy_threshold = False
    recognizer.energy_threshold = ENERGY_THRESHOLD
    microphone = sr.Microphone()
    engine = pyttsx3.init()
    used_prompts = 0
    messages = []

    while used_prompts <= PROMPT_LIMIT:
        
        response = ""
        
        input("Shell says: Press enter when ready for the next input")

        try:
            guess = recognize_speech_from_mic(recognizer, microphone)
        except sr.exceptions.WaitTimeoutError:
            print('Timed out.')
            engine.say('Timed out. Please try again')
            engine.runAndWait()
            continue

        if guess["error"]:
            print("ERROR: {}".format(guess["error"]))
            response = "There was an error. See standard out for details."
        
        elif not guess["transcription"]:
            reponse = "I'm sorry, I didn't catch that. What did you say?"
        else:
            print('You said: "{}"'.format(guess["transcription"]))
            if len(guess["transcription"]) > MAX_WORDS:
                response = "I'm sorry, you said too much. Please try rewording your prompt to be shorter."
            else:
                messages.append({"role": "user", "content": guess["transcription"]})
                used_prompts += 1
                response = openai.ChatCompletion.create(model="gpt-3.5-turbo",
                                                    messages=messages,
                                                    temperature=0,
                                                    max_tokens=MAX_WORDS*4)["choices"][0]["message"]["content"]
        
        print('AI said: "{}"\n\n'.format(response.strip()))
        engine.say(response)
        engine.runAndWait()
        messages.append({"role": "assistant", "content": response})