The Gemini API can transform text input into single speaker or multi-speaker
audio using native text-to-speech (TTS) generation capabilities.
Text-to-speech (TTS) generation is *[controllable](https://ai.google.dev/gemini-api/docs/speech-generation#controllable)* ,
meaning you can use natural language to structure interactions and guide the
*style* , *accent* , *pace* , and *tone* of the audio.

The TTS capability differs from speech generation provided through the
[Live API](https://ai.google.dev/gemini-api/docs/live), which is designed for interactive,
unstructured audio, and multimodal inputs and outputs. While the Live API excels
in dynamic conversational contexts, TTS through the Gemini API
is tailored for scenarios that require exact text recitation with fine-grained
control over style and sound, such as podcast or audiobook generation.

This guide shows you how to generate single-speaker and multi-speaker audio from
text.
| **Preview:** Native text-to-speech (TTS) is in [Preview](https://ai.google.dev/gemini-api/docs/models#preview).

## Before you begin

Ensure you use a Gemini 2.5 model variant with native text-to-speech (TTS) capabilities, as listed in the [Supported models](https://ai.google.dev/gemini-api/docs/speech-generation#supported-models) section. For optimal results, consider which model best fits your specific use case.

You may find it useful to [test the Gemini 2.5 TTS models in AI Studio](https://aistudio.google.com/generate-speech) before you start building.
| **Note:** TTS models accept text-only inputs and produce audio-only outputs. For a complete list of restrictions specific to TTS models, review the [Limitations](https://ai.google.dev/gemini-api/docs/speech-generation#limitations) section.

## Single-speaker text-to-speech

To convert text to single-speaker audio, set the response modality to "audio",
and pass a `SpeechConfig` object with `VoiceConfig` set.
You'll need to choose a voice name from the prebuilt [output voices](https://ai.google.dev/gemini-api/docs/speech-generation#voices).

This example saves the output audio from the model in a wave file:  

### Python

    from google import genai
    from google.genai import types
    import wave

    # Set up the wave file to save the output:
    def wave_file(filename, pcm, channels=1, rate=24000, sample_width=2):
       with wave.open(filename, "wb") as wf:
          wf.setnchannels(channels)
          wf.setsampwidth(sample_width)
          wf.setframerate(rate)
          wf.writeframes(pcm)

    client = genai.Client()

    response = client.models.generate_content(
       model="gemini-2.5-flash-preview-tts",
       contents="Say cheerfully: Have a wonderful day!",
       config=types.GenerateContentConfig(
          response_modalities=["AUDIO"],
          speech_config=types.SpeechConfig(
             voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                   voice_name='Kore',
                )
             )
          ),
       )
    )

    data = response.candidates[0].content.parts[0].inline_data.data

    file_name='out.wav'
    wave_file(file_name, data) # Saves the file to current directory

| For more code samples, refer to the
| "TTS - Get Started" file in the cookbooks repository:
|
|
| [View
| on GitHub](https://colab.research.google.com/github/google-gemini/cookbook/blob/main/quickstarts/Get_started_TTS.ipynb)

### JavaScript

    import {GoogleGenAI} from '@google/genai';
    import wav from 'wav';

    async function saveWaveFile(
       filename,
       pcmData,
       channels = 1,
       rate = 24000,
       sampleWidth = 2,
    ) {
       return new Promise((resolve, reject) => {
          const writer = new wav.FileWriter(filename, {
                channels,
                sampleRate: rate,
                bitDepth: sampleWidth * 8,
          });

          writer.on('finish', resolve);
          writer.on('error', reject);

          writer.write(pcmData);
          writer.end();
       });
    }

    async function main() {
       const ai = new GoogleGenAI({});

       const response = await ai.models.generateContent({
          model: "gemini-2.5-flash-preview-tts",
          contents: [{ parts: [{ text: 'Say cheerfully: Have a wonderful day!' }] }],
          config: {
                responseModalities: ['AUDIO'],
                speechConfig: {
                   voiceConfig: {
                      prebuiltVoiceConfig: { voiceName: 'Kore' },
                   },
                },
          },
       });

       const data = response.candidates?.[0]?.content?.parts?.[0]?.inlineData?.data;
       const audioBuffer = Buffer.from(data, 'base64');

       const fileName = 'out.wav';
       await saveWaveFile(fileName, audioBuffer);
    }
    await main();

### REST

    curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-tts:generateContent" \
      -H "x-goog-api-key: $GEMINI_API_KEY" \
      -X POST \
      -H "Content-Type: application/json" \
      -d '{
            "contents": [{
              "parts":[{
                "text": "Say cheerfully: Have a wonderful day!"
              }]
            }],
            "generationConfig": {
              "responseModalities": ["AUDIO"],
              "speechConfig": {
                "voiceConfig": {
                  "prebuiltVoiceConfig": {
                    "voiceName": "Kore"
                  }
                }
              }
            },
            "model": "gemini-2.5-flash-preview-tts",
        }' | jq -r '.candidates[0].content.parts[0].inlineData.data' | \
              base64 --decode >out.pcm
    # You may need to install ffmpeg.
    ffmpeg -f s16le -ar 24000 -ac 1 -i out.pcm out.wav

## Multi-speaker text-to-speech

For multi-speaker audio, you'll need a `MultiSpeakerVoiceConfig` object with
each speaker (up to 2) configured as a `SpeakerVoiceConfig`.
You'll need to define each `speaker` with the same names used in the
[prompt](https://ai.google.dev/gemini-api/docs/speech-generation#controllable):  

### Python

    from google import genai
    from google.genai import types
    import wave

    # Set up the wave file to save the output:
    def wave_file(filename, pcm, channels=1, rate=24000, sample_width=2):
       with wave.open(filename, "wb") as wf:
          wf.setnchannels(channels)
          wf.setsampwidth(sample_width)
          wf.setframerate(rate)
          wf.writeframes(pcm)

    client = genai.Client()

    prompt = """TTS the following conversation between Joe and Jane:
             Joe: How's it going today Jane?
             Jane: Not too bad, how about you?"""

    response = client.models.generate_content(
       model="gemini-2.5-flash-preview-tts",
       contents=prompt,
       config=types.GenerateContentConfig(
          response_modalities=["AUDIO"],
          speech_config=types.SpeechConfig(
             multi_speaker_voice_config=types.MultiSpeakerVoiceConfig(
                speaker_voice_configs=[
                   types.SpeakerVoiceConfig(
                      speaker='Joe',
                      voice_config=types.VoiceConfig(
                         prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name='Kore',
                         )
                      )
                   ),
                   types.SpeakerVoiceConfig(
                      speaker='Jane',
                      voice_config=types.VoiceConfig(
                         prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name='Puck',
                         )
                      )
                   ),
                ]
             )
          )
       )
    )

    data = response.candidates[0].content.parts[0].inline_data.data

    file_name='out.wav'
    wave_file(file_name, data) # Saves the file to current directory

### JavaScript

    import {GoogleGenAI} from '@google/genai';
    import wav from 'wav';

    async function saveWaveFile(
       filename,
       pcmData,
       channels = 1,
       rate = 24000,
       sampleWidth = 2,
    ) {
       return new Promise((resolve, reject) => {
          const writer = new wav.FileWriter(filename, {
                channels,
                sampleRate: rate,
                bitDepth: sampleWidth * 8,
          });

          writer.on('finish', resolve);
          writer.on('error', reject);

          writer.write(pcmData);
          writer.end();
       });
    }

    async function main() {
       const ai = new GoogleGenAI({});

       const prompt = `TTS the following conversation between Joe and Jane:
             Joe: How's it going today Jane?
             Jane: Not too bad, how about you?`;

       const response = await ai.models.generateContent({
          model: "gemini-2.5-flash-preview-tts",
          contents: [{ parts: [{ text: prompt }] }],
          config: {
                responseModalities: ['AUDIO'],
                speechConfig: {
                   multiSpeakerVoiceConfig: {
                      speakerVoiceConfigs: [
                            {
                               speaker: 'Joe',
                               voiceConfig: {
                                  prebuiltVoiceConfig: { voiceName: 'Kore' }
                               }
                            },
                            {
                               speaker: 'Jane',
                               voiceConfig: {
                                  prebuiltVoiceConfig: { voiceName: 'Puck' }
                               }
                            }
                      ]
                   }
                }
          }
       });

       const data = response.candidates?.[0]?.content?.parts?.[0]?.inlineData?.data;
       const audioBuffer = Buffer.from(data, 'base64');

       const fileName = 'out.wav';
       await saveWaveFile(fileName, audioBuffer);
    }

    await main();

### REST

    curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-tts:generateContent" \
      -H "x-goog-api-key: $GEMINI_API_KEY" \
      -X POST \
      -H "Content-Type: application/json" \
      -d '{
      "contents": [{
        "parts":[{
          "text": "TTS the following conversation between Joe and Jane:
                    Joe: Hows it going today Jane?
                    Jane: Not too bad, how about you?"
        }]
      }],
      "generationConfig": {
        "responseModalities": ["AUDIO"],
        "speechConfig": {
          "multiSpeakerVoiceConfig": {
            "speakerVoiceConfigs": [{
                "speaker": "Joe",
                "voiceConfig": {
                  "prebuiltVoiceConfig": {
                    "voiceName": "Kore"
                  }
                }
              }, {
                "speaker": "Jane",
                "voiceConfig": {
                  "prebuiltVoiceConfig": {
                    "voiceName": "Puck"
                  }
                }
              }]
          }
        }
      },
      "model": "gemini-2.5-flash-preview-tts",
    }' | jq -r '.candidates[0].content.parts[0].inlineData.data' | \
        base64 --decode > out.pcm
    # You may need to install ffmpeg.
    ffmpeg -f s16le -ar 24000 -ac 1 -i out.pcm out.wav

## Controlling speech style with prompts

You can control style, tone, accent, and pace using natural language prompts
for both single- and multi-speaker TTS.
For example, in a single-speaker prompt, you can say:  

    Say in an spooky whisper:
    "By the pricking of my thumbs...
    Something wicked this way comes"

In a multi-speaker prompt, provide the model with each speaker's name and
corresponding transcript. You can also provide guidance for each speaker
individually:  

    Make Speaker1 sound tired and bored, and Speaker2 sound excited and happy:

    Speaker1: So... what's on the agenda today?
    Speaker2: You're never going to guess!

Try using a [voice option](https://ai.google.dev/gemini-api/docs/speech-generation#voices) that corresponds to the style or emotion you
want to convey, to emphasize it even more. In the previous prompt, for example,
*Enceladus* 's breathiness might emphasize "tired" and "bored", while
*Puck*'s upbeat tone could complement "excited" and "happy".

## Generating a prompt to convert to audio

The TTS models only output audio, but you can use
[other models](https://ai.google.dev/gemini-api/docs/models) to generate a transcript first,
then pass that transcript to the TTS model to read aloud.  

### Python

    from google import genai
    from google.genai import types

    client = genai.Client()

    transcript = client.models.generate_content(
       model="gemini-2.0-flash",
       contents="""Generate a short transcript around 100 words that reads
                like it was clipped from a podcast by excited herpetologists.
                The hosts names are Dr. Anya and Liam.""").text

    response = client.models.generate_content(
       model="gemini-2.5-flash-preview-tts",
       contents=transcript,
       config=types.GenerateContentConfig(
          response_modalities=["AUDIO"],
          speech_config=types.SpeechConfig(
             multi_speaker_voice_config=types.MultiSpeakerVoiceConfig(
                speaker_voice_configs=[
                   types.SpeakerVoiceConfig(
                      speaker='Dr. Anya',
                      voice_config=types.VoiceConfig(
                         prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name='Kore',
                         )
                      )
                   ),
                   types.SpeakerVoiceConfig(
                      speaker='Liam',
                      voice_config=types.VoiceConfig(
                         prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name='Puck',
                         )
                      )
                   ),
                ]
             )
          )
       )
    )

    # ...Code to stream or save the output

### JavaScript

    import { GoogleGenAI } from "@google/genai";

    const ai = new GoogleGenAI({});

    async function main() {

    const transcript = await ai.models.generateContent({
       model: "gemini-2.0-flash",
       contents: "Generate a short transcript around 100 words that reads like it was clipped from a podcast by excited herpetologists. The hosts names are Dr. Anya and Liam.",
       })

    const response = await ai.models.generateContent({
       model: "gemini-2.5-flash-preview-tts",
       contents: transcript,
       config: {
          responseModalities: ['AUDIO'],
          speechConfig: {
             multiSpeakerVoiceConfig: {
                speakerVoiceConfigs: [
                       {
                         speaker: "Dr. Anya",
                         voiceConfig: {
                            prebuiltVoiceConfig: {voiceName: "Kore"},
                         }
                      },
                      {
                         speaker: "Liam",
                         voiceConfig: {
                            prebuiltVoiceConfig: {voiceName: "Puck"},
                        }
                      }
                    ]
                  }
                }
          }
      });
    }
    // ..JavaScript code for exporting .wav file for output audio

    await main();

## Voice options

TTS models support the following 30 voice options in the `voice_name` field:  

|-----------------------------|-----------------------------------|---------------------------------|
| **Zephyr** -- *Bright*      | **Puck** -- *Upbeat*              | **Charon** -- *Informative*     |
| **Kore** -- *Firm*          | **Fenrir** -- *Excitable*         | **Leda** -- *Youthful*          |
| **Orus** -- *Firm*          | **Aoede** -- *Breezy*             | **Callirrhoe** -- *Easy-going*  |
| **Autonoe** -- *Bright*     | **Enceladus** -- *Breathy*        | **Iapetus** -- *Clear*          |
| **Umbriel** -- *Easy-going* | **Algieba** -- *Smooth*           | **Despina** -- *Smooth*         |
| **Erinome** -- *Clear*      | **Algenib** -- *Gravelly*         | **Rasalgethi** -- *Informative* |
| **Laomedeia** -- *Upbeat*   | **Achernar** -- *Soft*            | **Alnilam** -- *Firm*           |
| **Schedar** -- *Even*       | **Gacrux** -- *Mature*            | **Pulcherrima** -- *Forward*    |
| **Achird** -- *Friendly*    | **Zubenelgenubi** -- *Casual*     | **Vindemiatrix** -- *Gentle*    |
| **Sadachbia** -- *Lively*   | **Sadaltager** -- *Knowledgeable* | **Sulafat** -- *Warm*           |

You can hear all the voice options in
[AI Studio](https://aistudio.google.com/generate-speech).

## Supported languages

The TTS models detect the input language automatically. They support the
following 24 languages:

|        Language        |        BCP-47 Code        |       Language       | BCP-47 Code |
|------------------------|---------------------------|----------------------|-------------|
| Arabic (Egyptian)      | `ar-EG`                   | German (Germany)     | `de-DE`     |
| English (US)           | `en-US`                   | Spanish (US)         | `es-US`     |
| French (France)        | `fr-FR`                   | Hindi (India)        | `hi-IN`     |
| Indonesian (Indonesia) | `id-ID`                   | Italian (Italy)      | `it-IT`     |
| Japanese (Japan)       | `ja-JP`                   | Korean (Korea)       | `ko-KR`     |
| Portuguese (Brazil)    | `pt-BR`                   | Russian (Russia)     | `ru-RU`     |
| Dutch (Netherlands)    | `nl-NL`                   | Polish (Poland)      | `pl-PL`     |
| Thai (Thailand)        | `th-TH`                   | Turkish (Turkey)     | `tr-TR`     |
| Vietnamese (Vietnam)   | `vi-VN`                   | Romanian (Romania)   | `ro-RO`     |
| Ukrainian (Ukraine)    | `uk-UA`                   | Bengali (Bangladesh) | `bn-BD`     |
| English (India)        | `en-IN` \& `hi-IN` bundle | Marathi (India)      | `mr-IN`     |
| Tamil (India)          | `ta-IN`                   | Telugu (India)       | `te-IN`     |

## Supported models

|                                                   Model                                                   | Single speaker | Multispeaker |
|-----------------------------------------------------------------------------------------------------------|----------------|--------------|
| [Gemini 2.5 Flash Preview TTS](https://ai.google.dev/gemini-api/docs/models#gemini-2.5-flash-preview-tts) | ✔️             | ✔️           |
| [Gemini 2.5 Pro Preview TTS](https://ai.google.dev/gemini-api/docs/models#gemini-2.5-pro-preview-tts)     | ✔️             | ✔️           |

## Limitations

- TTS models can only receive text inputs and generate audio outputs.
- A TTS session has a [context window](https://ai.google.dev/gemini-api/docs/long-context) limit of 32k tokens.
- Review [Languages](https://ai.google.dev/gemini-api/docs/speech-generation#languages) section for language support.

## What's next

- Try the [audio generation cookbook](https://colab.research.google.com/github/google-gemini/cookbook/blob/main/quickstarts/Get_started_TTS.ipynb).
- Gemini's [Live API](https://ai.google.dev/gemini-api/docs/live) offers interactive audio generation options you can interleave with other modalities.
- For working with audio *inputs* , visit the [Audio understanding](https://ai.google.dev/gemini-api/docs/audio) guide.

---
voices:

# --------------------------------------------------------------------

# Каталог голосов, составленный на основе аналитического отчета

# Источник данных: Таблица 1, "Голоса Gemini TTS в 2025"

# --------------------------------------------------------------------

  achernar:
    name: "Achernar"
    gender: "Мужской"
    description: "Чистый мужской голос среднего диапазона с дружелюбным и увлекательным тоном. Передает энтузиазм и доступность, не будучи чрезмерно энергичным. Идеален для видео-инструкций, дружелюбного корпоративного повествования, вступлений к подкастам."
  
  achird:
    name: "Achird"
    gender: "Женский"
    description: "Молодой женский голос средне-высокого тона, чистый, с легкой придыхательностью и вопросительной интонацией. Звучит дружелюбно и доступно, подходит для современного контента. Лучшее применение: учебные модули для молодой аудитории, дружелюбные туториалы для приложений, голос молодого персонажа."

  algenib:
    name: "Algenib"
    gender: "Женский"
    description: "Теплый, уверенный женский голос среднего диапазона с хорошей четкостью. Излучает дружелюбный авторитет и опыт. Лучшее применение: корпоративные презентации, документальное повествование, роли зрелых, но дружелюбных персонажей."

  alnilam:
    name: "Alnilam"
    gender: "Мужской"
    description: "Энергичный мужской голос средне-низкого тона, несущий ощущение воодушевления и ясности. Имеет несколько рекламное, восторженное качество, очень прямой. Лучшее применение: рекламные ролики, промо-материалы, объявления о мероприятиях."

  aoede:
    name: "Aoede"
    gender: "Женский"
    description: "Чистый, разговорный женский голос среднего диапазона с вдумчивым, увлекательным качеством. Звучит интеллигентно и артикулированно, легко слушать в течение длительного времени. Лучшее применение: ведение подкастов, электронное обучение, повествование в информационном контенте."

  autonoe:
    name: "Autonoe"
    gender: "Женский"
    description: "Яркий, зрелый женский голос с резонансным и вдумчивым качеством. Передает мудрость и опыт, со спокойным и размеренным темпом. Идеален для документального повествования, озвучивания аудиокниг (серьезная нон-фикшн), авторитетных ролей."

  callirrhoe:
    name: "Callirrhoe"
    gender: "Женский"
    description: "Уверенный, ясный женский голос среднего диапазона, излучающий профессионализм и энергию. Артикулированный и прямой, хорошо подходит для эффективной передачи информации. Лучшее применение: бизнес-презентации, корпоративное обучение, системы IVR."

  charon:
    name: "Charon"
    gender: "Мужской"
    description: "Гладкий, разговорный мужской голос средне-низкого тона, звучащий уверенно и доступно. Несет в себе мягкий авторитет и надежность. Лучшее применение: повествование в подкастах, видео-инструкции, корпоративные коммуникации."

  despina:
    name: "Despina"
    gender: "Женский"
    description: "Теплый и располагающий женский голос с ясным средним диапазоном. Звучит дружелюбно, надежно и увлекательно, с приятной гладкостью. Лучшее применение: рекламные ролики (особенно лайфстайл/семейные), записи для службы поддержки, приветственные сообщения."

  enceladus:
    name: "Enceladus"
    gender: "Мужской"
    description: "Дыхательный, энергичный и восторженный мужской голос среднего диапазона, идеально подходящий для передачи волнения. Четкая и впечатляющая подача с легким 'промо' оттенком. Лучшее применение: промо-видео, объявления о мероприятиях, высокоэнергетическая реклама."

  erinome:
    name: "Erinome"
    gender: "Женский"
    description: "Профессиональный и артикулированный женский голос с несколько более низким средним диапазоном и вдумчивой, размеренной подачей. Передает интеллект и самообладание с оттенком утонченности. Лучшее применение: образовательный контент, корпоративное повествование, аудиогиды в музеях."

  fenrir:
    name: "Fenrir"
    gender: "Мужской"
    description: "Дружелюбный и ясный мужской голос среднего диапазона, демонстрирующий разговорный и доступный стиль. Увлекательный и легкий для прослушивания, с естественной подачей. Лучшее применение: видео-инструкции, подкастинг, контент для электронного обучения."

  gacrux:
    name: "Gacrux"
    gender: "Женский"
    description: "Гладкий, уверенный женский голос средне-низкого тона с ясным, авторитетным, но доступным тоном. Эффективно проецирует опыт и знания. Идеален для документального повествования, корпоративных презентаций, аудиокниг (нон-фикшн)."

  iapetus:
    name: "Iapetus"
    gender: "Мужской"
    description: "Дружелюбный мужской голос среднего тона с непринужденным качеством 'простого парня'. Звучит доступно и узнаваемо, хорошо подходит для неформального общения. Лучшее применение: неформальные туториалы, влоги, разговорный маркетинг."

  kore:
    name: "Kore"
    gender: "Женский"
    description: "Энергичный и молодой женский голос средне-высокого тона, передающий уверенность и энтузиазм. Чистый и яркий, с живым, увлекательным качеством. Лучшее применение: динамичная реклама, туториалы для молодой аудитории, голос анимационного персонажа."

  laomedeia:
    name: "Laomedeia"
    gender: "Женский"
    description: "Ясный, разговорный женский голос среднего диапазона, обладающий вопросительным и увлекательным тоном. Звучит дружелюбно и интеллигентно, похож на Aoede, но, возможно, немного более энергичный. Лучшее применение: электронное обучение, видео-инструкции, ведение подкастов."

  leda:
    name: "Leda"
    gender: "Женский"
    description: "Сдержанный и профессиональный женский голос, среднечастотный с несколько более низким резонансом, передающий авторитет и спокойствие. Артикулированный и размеренный, с утонченным и надежным ощущением. Лучшее применение: корпоративное обучение, серьезное повествование, официальные объявления."

  orus:
    name: "Orus"
    gender: "Мужской"
    description: "Зрелый мужской голос с более глубоким, резонансным качеством, передающий вдумчивость и опыт. Успокаивающий и авторитетный, с размеренным, обдуманным темпом. Лучшее применение: документальное повествование, аудиокниги (серьезная проза/нон-фикшн), голос персонажа (мудрый старец)."

  puck:
    name: "Puck"
    gender: "Мужской"
    description: "Ясный и прямой мужской голос среднего диапазона, звучащий уверенно и доступно. Имеет несколько неформальное ощущение 'парня по соседству', надежный. Лучшее применение: видео-инструкции, неформальные корпоративные коммуникации, дружелюбные демонстрации продуктов."

  pulcherrima:
    name: "Pulcherrima"
    gender: "Женский"
    description: "Прямой, яркий, энергичный женский голос средне-высокого тона, звучащий молодо и восторженно. Ясная и увлекательная подача, очень оптимистичная. Лучшее применение: оптимистичная реклама, туториалы, голос персонажа для анимации или контента для молодежи."

  rasalgethi:
    name: "Rasalgethi"
    gender: "Мужской"
    description: "Информативный, разговорный мужской голос среднего диапазона с легкой гнусавостью и вопросительным качеством. Доступный, но отчетливый, с вдумчивой, вопросительной интонацией. Лучшее применение: обсуждения в подкастах, работа над персонажем (эксцентричный), неформальные объяснения."

  sadachbia:
    name: "Sadachbia"
    gender: "Мужской"
    description: "Живой, более глубокий мужской голос с легкой хрипотцой или текстурой, излучающий уверенность и 'крутой', расслабленный авторитет. Запоминающийся и отличительный, с оттенком серьезности. Лучшее применение: трейлеры к фильмам, смелая реклама, голос персонажа (крутой парень/бунтарь)."

  sadaltager:
    name: "Sadaltager"
    gender: "Мужской"
    description: "Знающий, дружелюбный и восторженный мужской голос с ясным средним диапазоном, хорошо подходящий для презентаций. Увлекательный и профессиональный, с хорошей артикуляцией. Лучшее применение: корпоративные презентации, обучающие видео, ведение вебинаров."

  schedar:
    name: "Schedar"
    gender: "Мужской"
    description: "Ровный, дружелюбный мужской голос среднего тона с неформальным, доступным качеством. Передает ощущение приземленности и узнаваемости, легок для понимания. Лучшее применение: непринужденные туториалы, влоги, дружелюбные объяснения продуктов."

  sulafat:
    name: "Sulafat"
    gender: "Женский"
    description: "Теплый, уверенный женский голос с ясным средним диапазоном, звучащий убедительно и артикулированно. Проецирует интеллект и дружелюбие, с увлекательным присутствием. Лучшее применение: корпоративное повествование, электронное обучение, убедительный маркетинг."

  umbriel:
    name: "Umbriel"
    gender: "Мужской"
    description: "Спокойный, гладкий мужской голос средне-низкого тона, передающий авторитет, но остающийся дружелюбным и увлекательным. Отличная ясность для повествования, с надежным и знающим тоном. Лучшее применение: документальное повествование, корпоративные истории, озвучивание аудиокниг."

  vindemiatrix:
    name: "Vindemiatrix"
    gender: "Женский"
    description: "Нежный, спокойный, вдумчивый женский голос средне-низкого тона, звучащий зрело и сдержанно. Передает мудрость и мягкий авторитет, с гладким, успокаивающим качеством. Лучшее применение: руководства по медитации, повествование для рефлексивного контента, голоса зрелых персонажей."

  zephyr:
    name: "Zephyr"
    gender: "Женский"
    description: "Яркий, энергичный и светлый женский голос с ясным средним диапазоном, звучащий живо и восторженно. Излучает позитив и молодость, очень увлекательный. Лучшее применение: оптимистичная реклама, детский контент, дружелюбный IVR."

  zubenelgenubi:
    name: "Zubenelgenubi"
    gender: "Мужской"
    description: "Непринужденный, глубокий, резонансный мужской голос, передающий сильный авторитет и серьезность. Привлекает внимание мощной и размеренной подачей. Лучшее применение: трейлеры к фильмам (эпические), официальные объявления, авторитетное повествование."


algieba:
    name: "Algieba"
    gender: "Мужской"
    description: "Спокойный (Calm)"
