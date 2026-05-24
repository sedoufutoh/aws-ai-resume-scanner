import json
import urllib.request
import urllib.error
import os
import re

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
GEMINI_URL = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=' + GEMINI_API_KEY

CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Allow-Methods': 'POST, OPTIONS'
}

def build_general_prompt(resume_text):
    prompt = "You are an expert resume consultant. Analyze this resume comprehensively.\n\n"
    prompt += "RESUME:\n" + resume_text + "\n\n"
    prompt += "Provide analysis with these exact sections using ### headers:\n\n"
    prompt += "### Overall Resume Score\n"
    prompt += "Score: X/100. Explain in 3-4 sentences.\n\n"
    prompt += "### Overview\n"
    prompt += "3-4 sentence overall assessment.\n\n"
    prompt += "### Hard Skills\n"
    prompt += "List technical skills found. Format: **Skill Name** - X mentions\n\n"
    prompt += "### Soft Skills\n"
    prompt += "List interpersonal skills found. Format: **Skill Name** - X mentions\n\n"
    prompt += "### Improvement Recommendations\n"
    prompt += "Give 5 specific numbered recommendations.\n\n"
    prompt += "### Summary\n"
    prompt += "2-3 sentence conclusion with the most important action to take."
    return prompt

def build_specific_prompt(resume_text, job_description):
    prompt = "You are an expert resume consultant. Analyze this resume against the job description.\n\n"
    prompt += "RESUME:\n" + resume_text + "\n\n"
    prompt += "JOB DESCRIPTION:\n" + job_description + "\n\n"
    prompt += "Provide analysis with these exact sections using ### headers:\n\n"
    prompt += "### ATS Compatibility Score\n"
    prompt += "Score: X/100. Explain in 3-4 sentences.\n\n"
    prompt += "### Overview\n"
    prompt += "3-4 sentence overall assessment of fit.\n\n"
    prompt += "### Keywords Present\n"
    prompt += "List keywords found in both resume and job description.\n\n"
    prompt += "### Keywords Missing\n"
    prompt += "List important keywords from job description not in resume.\n\n"
    prompt += "### Hard Skills\n"
    prompt += "List technical skills found. Format: **Skill Name** - X mentions\n\n"
    prompt += "### Soft Skills\n"
    prompt += "List interpersonal skills found. Format: **Skill Name** - X mentions\n\n"
    prompt += "### Improvement Recommendations\n"
    prompt += "Give 5 specific numbered recommendations.\n\n"
    prompt += "### Summary\n"
    prompt += "2-3 sentence conclusion with the most important action to take."
    return prompt

def call_gemini(prompt):
    payload = json.dumps({
        'contents': [{'parts': [{'text': prompt}]}],
        'generationConfig': {'maxOutputTokens': 3000, 'temperature': 0.4}
    }).encode('utf-8')

    req = urllib.request.Request(
        GEMINI_URL,
        data=payload,
        headers={'Content-Type': 'application/json'},
        method='POST'
    )

    with urllib.request.urlopen(req, timeout=55) as response:
        result = json.loads(response.read().decode('utf-8'))
        return result['candidates'][0]['content']['parts'][0]['text']

def extract_score(text):
    match = re.search(r'[Ss]core[:\s]+(\d{1,3})\s*(?:out of|\/)\s*100', text[:800])
    if match:
        score = int(match.group(1))
        if 0 <= score <= 100:
            return str(score) + '/100'
    return None

def lambda_handler(event, context):
    method = event.get('requestContext', {}).get('http', {}).get('method', 'POST')

    if method == 'OPTIONS':
        return {'statusCode': 200, 'headers': CORS_HEADERS, 'body': ''}

    try:
        body = json.loads(event.get('body', '{}'))
        mode = body.get('mode', 'general')
        resume_text = body.get('resumeText', '').strip()
        job_description = body.get('jobDescription', '')

        if not resume_text or len(resume_text) < 50:
            return {
                'statusCode': 400,
                'headers': CORS_HEADERS,
                'body': json.dumps({'error': 'Resume text is too short. Please paste your resume text.'})
            }

        if len(resume_text) > 8000:
            resume_text = resume_text[:8000]

        if mode == 'specific' and job_description:
            prompt = build_specific_prompt(resume_text, job_description)
        else:
            prompt = build_general_prompt(resume_text)

        analysis = call_gemini(prompt)
        score = extract_score(analysis)

        return {
            'statusCode': 200,
            'headers': CORS_HEADERS,
            'body': json.dumps({'analysis': analysis, 'score': score, 'mode': mode})
        }

    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        return {
            'statusCode': 500,
            'headers': CORS_HEADERS,
            'body': json.dumps({'error': 'Gemini API error: ' + error_body})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': CORS_HEADERS,
            'body': json.dumps({'error': 'Error: ' + str(e)})
        }
