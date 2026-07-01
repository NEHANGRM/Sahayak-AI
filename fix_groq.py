with open("utils.py", "r") as f:
    content = f.read()

# Fix review_complaint
old_review = """            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a senior public governance auditor. Analyze the complaint and provide a structured review in JSON format. Do not recommend priority labels like Critical/High directly, but recommend a priority_adjustment between -0.15 and +0.15 based on public safety, infrastructure, and vulnerability risk assessment. Return ONLY a valid JSON object."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            import json
            result = json.loads(completion.choices[0].message.content)
            return self._parse_result(result)"""

new_review = """            import time
            import json
            
            retries = 3
            for attempt in range(retries):
                try:
                    completion = self.client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": "You are a senior public governance auditor. Analyze the complaint and provide a structured review in JSON format. Do not recommend priority labels like Critical/High directly, but recommend a priority_adjustment between -0.15 and +0.15 based on public safety, infrastructure, and vulnerability risk assessment. Return ONLY a valid JSON object without any markdown code blocks."},
                            {"role": "user", "content": prompt}
                        ]
                    )
                    
                    text = completion.choices[0].message.content.strip()
                    if text.startswith("```json"): text = text[7:]
                    elif text.startswith("```"): text = text[3:]
                    if text.endswith("```"): text = text[:-3]
                    
                    result = json.loads(text.strip())
                    return self._parse_result(result)
                except Exception as e:
                    if 'rate_limit_exceeded' in str(e) or '429' in str(e):
                        if attempt < retries - 1:
                            time.sleep(2 * (attempt + 1))
                            continue
                    raise e"""

# Fix generate_suggestions
old_sugg = """            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a senior public governance assistant. Return ONLY a valid JSON object."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            import json
            result = json.loads(completion.choices[0].message.content)"""

new_sugg = """            import time
            import json
            
            retries = 3
            result = {}
            for attempt in range(retries):
                try:
                    completion = self.client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": "You are a senior public governance assistant. Return ONLY a valid JSON object without any markdown code blocks."},
                            {"role": "user", "content": prompt}
                        ]
                    )
                    
                    text = completion.choices[0].message.content.strip()
                    if text.startswith("```json"): text = text[7:]
                    elif text.startswith("```"): text = text[3:]
                    if text.endswith("```"): text = text[:-3]
                    
                    result = json.loads(text.strip())
                    break
                except Exception as e:
                    if 'rate_limit_exceeded' in str(e) or '429' in str(e):
                        if attempt < retries - 1:
                            time.sleep(2 * (attempt + 1))
                            continue
                    raise e"""

content = content.replace(old_review, new_review)
content = content.replace(old_sugg, new_sugg)

with open("utils.py", "w") as f:
    f.write(content)
print("utils.py patched successfully")
