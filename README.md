# AI Resume Scanner | [Live Demo](https://www.sedoufutoh.com/resume-scanner)

An AI-powered resume analysis tool built on AWS serverless infrastructure and Google Gemini API. Paste a resume and a job description — get instant, structured feedback on fit, strengths, and gaps.

-----

## 1. Problem Statement

Job seekers spend hours tailoring resumes without knowing how well they actually match a role. Recruiters and applicant tracking systems (ATS) filter out candidates before a human ever reads their resume.

This tool solves both sides of that problem:

- **For job seekers:** Instant, AI-generated feedback on resume-to-job alignment before applying
- **For recruiters / HR teams:** A lightweight, scalable screening assistant that requires no infrastructure investment

-----

## 2. Why I Built This

Manual resume review is time-consuming and inconsistent. After personally going through a career transition (14 years as a chemistry teacher → cloud/IT professional), I experienced firsthand how hard it is to know whether a resume will resonate with a recruiter.

I wanted a tool that gives real, actionable feedback — not generic tips. Building it on AWS serverless architecture meant zero server management, automatic scaling, and near-zero cost.

-----

## 3. Architecture

```
User (Browser)
     │
     ▼
CloudFront (CDN + HTTPS)
     │
     ▼
S3 (Static frontend — resume-scanner.html)
     │  [user submits resume + JD text]
     ▼
Lambda Function URL (HTTPS endpoint)
     │
     ▼
Lambda Function (Python 3.12)
     │  [builds prompt, calls Gemini API]
     ▼
Google Gemini API (gemini-2.5-flash)
     │  [returns structured analysis]
     ▼
Lambda → Response → Browser
```

**Key design decision:** No API Gateway. The Lambda Function URL handles HTTPS directly, reducing cost and complexity. CORS is managed entirely inside the Lambda response headers.

-----

## 4. AWS Services Used

|Service                |Role                                                             |
|-----------------------|-----------------------------------------------------------------|
|**AWS Lambda**         |Core compute — runs the Python function that calls Gemini API    |
|**Lambda Function URL**|Exposes Lambda as a public HTTPS endpoint (no API Gateway needed)|
|**Amazon S3**          |Hosts the static HTML frontend                                   |
|**Amazon CloudFront**  |CDN — delivers the frontend globally with HTTPS                  |
|**AWS IAM**            |Least-privilege execution role for Lambda                        |

**External:** Google Gemini API (`gemini-2.5-flash`) — AI model for resume analysis

-----

## 5. Key Concepts Demonstrated

- **Serverless architecture** — no servers to manage, auto-scaling, pay-per-use
- **Lambda Function URL** — direct HTTPS invocation without API Gateway overhead
- **CORS configuration** — handled entirely in Lambda response headers (not at the Function URL level)
- **Least-privilege IAM** — Lambda execution role scoped to minimum required permissions
- **Static + dynamic separation** — frontend on S3/CloudFront, logic on Lambda
- **External API integration** — Gemini API called securely from Lambda backend
- **Prompt engineering** — structured prompt produces consistent, actionable AI output

-----

## 6. Business Value

|Metric                    |Value                                                                    |
|--------------------------|-------------------------------------------------------------------------|
|**Estimated monthly cost**|~$0.05 (Lambda free tier + minimal invocations)                          |
|**Response time**         |~3–8 seconds per analysis                                                |
|**Scalability**           |Handles concurrent users automatically — no infrastructure changes needed|
|**Maintenance**           |Zero server patching, zero OS management                                 |

Real-world application: HR teams at small businesses could deploy this as a lightweight pre-screening tool without paying for enterprise ATS software.

-----

## 7. Deployment Guide

### Prerequisites

- AWS account with IAM permissions for Lambda, S3, CloudFront
- Google Gemini API key ([get one free at Google AI Studio](https://aistudio.google.com/))
- Python 3.12

### Step 1 — Create the Lambda Function

1. Go to **AWS Lambda → Create function**
1. Runtime: **Python 3.12**
1. Architecture: **x86_64**
1. Memory: **256 MB** | Timeout: **55 seconds**
1. Paste the contents of `lambda_function.py`
1. Add environment variable: `GEMINI_API_KEY = <your-key>`

**Why:** Lambda handles all backend logic. The 55-second timeout accommodates Gemini API response time.

### Step 2 — Create a Lambda Function URL

1. In your Lambda function → **Configuration → Function URL**
1. Auth type: **NONE** (public endpoint)
1. CORS: **Leave disabled** — CORS is handled in the Lambda code itself

**Why:** Function URL gives a public HTTPS endpoint without API Gateway cost. CORS must be handled in the Lambda response, not the Function URL settings — enabling both causes header conflicts.

### Step 3 — Create S3 Bucket

1. Create a bucket (e.g., `resume-scanner-frontend`)
1. **Block all public access** — CloudFront will serve the content
1. Upload `resume-scanner.html`
1. Update the `fetch()` URL in the HTML to point to your Lambda Function URL

### Step 4 — Create CloudFront Distribution

1. Origin: your S3 bucket
1. Use **Origin Access Control (OAC)** — not OAI
1. Default root object: `resume-scanner.html`
1. Update S3 bucket policy to allow CloudFront OAC access

**Why:** CloudFront provides HTTPS, caching, and global delivery. Direct S3 public access is not recommended.

### Step 5 — Test End to End

1. Visit your CloudFront URL
1. Paste a sample resume and job description
1. Click **Analyze**
1. Expected: structured AI feedback within ~5–8 seconds

-----

## 8. Challenges & Resolutions

### Challenge 1 — CORS errors blocking all API calls

**Problem:** After deploying the Lambda Function URL, every request from the browser was blocked by CORS policy.

**What I tried first:** Enabling CORS at the Function URL level in the AWS console — this did not work and made the issue worse (duplicate headers).

**Resolution:** Disabled CORS at the Function URL entirely. Added CORS headers directly in the Lambda response:

```python
return {
    "statusCode": 200,
    "headers": {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Allow-Methods": "POST, OPTIONS"
    },
    "body": json.dumps({"result": analysis})
}
```

**Lesson:** When using Lambda Function URLs, CORS must be managed in one place only — the Lambda response code. Enabling it at both levels causes conflicting headers.

-----

### Challenge 2 — Gemini API timeout on cold starts

**Problem:** First invocations occasionally timed out before Gemini responded.

**Resolution:** Increased Lambda timeout from 30 to 55 seconds. Lambda’s default 3-second timeout is far too short for external AI API calls.

-----

### Challenge 3 — CloudFront serving stale HTML

**Problem:** After updating `resume-scanner.html` in S3, CloudFront continued serving the old version.

**Resolution:** Created a CloudFront cache invalidation (`/*`) after each upload. Added this as a standard step in the deployment workflow.

-----

## 9. Lessons Learned

- **CORS is a browser security feature, not a server feature** — the fix must come from the server response headers, not the infrastructure layer
- **Lambda Function URL is a viable API Gateway alternative** for simple single-endpoint use cases — lower cost, less configuration
- **Always invalidate CloudFront cache after S3 updates** — the CDN will serve stale content indefinitely otherwise
- **Prompt structure matters** — a well-structured system prompt produces consistent, formatted AI output; a vague one produces unpredictable results

-----

## 10. Live Demo & Repository

- **Live:** [sedoufutoh.com/resume-scanner](https://www.sedoufutoh.com/resume-scanner)
- **Repo:** [github.com/sedoufutoh/aws-ai-resume-scanner](https://github.com/sedoufutoh/aws-ai-resume-scanner)
- **Stack:** AWS Lambda · Lambda Function URL · S3 · CloudFront · IAM · Google Gemini API
- **Cost:** ~$0.05/month

-----

*Part of my AWS cloud portfolio — built while preparing for the AWS Solutions Architect Associate (SAA-C03) certification.*
