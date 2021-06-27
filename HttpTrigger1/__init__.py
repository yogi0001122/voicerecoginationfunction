import logging
import azure.functions as func
import base64
import os
import azure.cognitiveservices.speech as speechsdk
import time
import datetime
import tempfile


speech_key, service_region = "<Voice to test Congnitive service Key>", "<Region>"


def speech_recognize_continuous_from_file(weatherfilename):
    all_results = []


    def handle_final_result(evt):
         all_results.append(evt.result.text)

    """performs continuous speech recognition with input from an audio file new"""
    # <SpeechContinuousRecognitionWithFile>
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
    audio_config = speechsdk.audio.AudioConfig(filename=weatherfilename)

    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)  

    done = False

    def stop_cb(evt):
        """callback that signals to stop continuous recognition upon receiving an event `evt`"""
        print('CLOSING on {}'.format(evt))
        nonlocal done
        done = True

    #Appends the recognized text to the all_results variable.
    speech_recognizer.recognized.connect(handle_final_result)
    
    # Connect callbacks to the events fired by the speech recognizer
    speech_recognizer.recognizing.connect(lambda evt: print('RECOGNIZING: {}'.format(evt)))
    speech_recognizer.recognized.connect(lambda evt: print('RECOGNIZED: {}'.format(evt)))
    speech_recognizer.session_started.connect(lambda evt: print('SESSION STARTED: {}'.format(evt)))
    speech_recognizer.session_stopped.connect(lambda evt: print('SESSION STOPPED {}'.format(evt)))
    speech_recognizer.canceled.connect(lambda evt: print('CANCELED {}'.format(evt)))
    # stop continuous recognition on either session stopped or canceled events
    speech_recognizer.session_stopped.connect(stop_cb)
    speech_recognizer.canceled.connect(stop_cb)

    # Start continuous speech recognition
    speech_recognizer.start_continuous_recognition()
    while not done:
        time.sleep(.5)

    speech_recognizer.stop_continuous_recognition()
    # </SpeechContinuousRecognitionWithFile>
    return all_results

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    name = req.params.get('name')
    filename = name
    result = ''
    print (req.url)   
    if not name:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            name = req_body.get('name')
            content = req_body.get('contentBytes')

    print (f"Hello, {name} . This HTTP triggered function executed successfully.")

    dir_path = tempfile.gettempdir()
    download_file_path = os.path.join(dir_path, str(name))
    print("Downloading blob to " + download_file_path)

    try: 
        with open(download_file_path, "wb") as download_file:
            download_file.write(base64.b64decode(content))        
    except (IOError, EOFError) as e:
        print("Testing multiple exceptions. {}".format(e.args[-1]))


    logging.info('Calling voicetotext_recog logic function')
    all_results = speech_recognize_continuous_from_file(download_file_path)
    print("Printing all results: along with new output")
    #print (all_results)
    result = ''
    for line in all_results:
        result += line

    print("Remove Downloaded files...")
    os.remove(download_file_path)
    
    if name:
        return func.HttpResponse(f"{result}")
    else:
        return func.HttpResponse(
             "This HTTP triggered function executed successfully. Pass a name in the query string or in the request body for a personalized response.",
             status_code=200
        )
    
