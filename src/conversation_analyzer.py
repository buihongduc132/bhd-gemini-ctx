#!/usr/bin/env python3
"""
Conversation Analyzer for Gemini Extractions
Analyzes extracted conversations and provides insights and statistics.
"""

import json
import re
from pathlib import Path
from datetime import datetime
from collections import Counter
import statistics

class ConversationAnalyzer:
    def __init__(self, extracts_dir="gemini_extracts"):
        self.extracts_dir = Path(extracts_dir)
    
    def analyze_conversation(self, json_file_path):
        """Analyze a single conversation JSON file."""
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        analysis = {
            "title": data.get("title", "Unknown"),
            "url": data.get("url", ""),
            "extracted_at": data.get("extracted_at", ""),
            "total_messages": data.get("message_count", 0),
            "user_messages": 0,
            "assistant_messages": 0,
            "message_lengths": [],
            "topics_mentioned": [],
            "code_blocks": 0,
            "questions_asked": 0,
            "avg_message_length": 0,
            "conversation_flow": [],
            "technical_terms": [],
            "key_insights": []
        }
        
        messages = data.get("messages", [])
        
        for msg in messages:
            sender = msg.get("sender", "unknown")
            content = msg.get("content", "")
            msg_length = len(content)
            
            analysis["message_lengths"].append(msg_length)
            analysis["conversation_flow"].append({
                "sender": sender,
                "length": msg_length,
                "timestamp": msg.get("timestamp", "")
            })
            
            if sender == "user":
                analysis["user_messages"] += 1
                # Count questions
                if "?" in content:
                    analysis["questions_asked"] += content.count("?")
            elif sender == "assistant":
                analysis["assistant_messages"] += 1
            
            # Detect code blocks
            code_patterns = [
                r'```[\s\S]*?```',  # Markdown code blocks
                r'`[^`]+`',         # Inline code
                r'<code>[\s\S]*?</code>',  # HTML code tags
            ]
            
            for pattern in code_patterns:
                analysis["code_blocks"] += len(re.findall(pattern, content))
            
            # Extract technical terms and topics
            technical_terms = self.extract_technical_terms(content)
            analysis["technical_terms"].extend(technical_terms)
            
            topics = self.extract_topics(content)
            analysis["topics_mentioned"].extend(topics)
        
        # Calculate statistics
        if analysis["message_lengths"]:
            analysis["avg_message_length"] = statistics.mean(analysis["message_lengths"])
            analysis["median_message_length"] = statistics.median(analysis["message_lengths"])
            analysis["max_message_length"] = max(analysis["message_lengths"])
            analysis["min_message_length"] = min(analysis["message_lengths"])
        
        # Count unique technical terms and topics
        analysis["unique_technical_terms"] = list(set(analysis["technical_terms"]))
        analysis["unique_topics"] = list(set(analysis["topics_mentioned"]))
        
        # Generate insights
        analysis["key_insights"] = self.generate_insights(analysis)
        
        return analysis
    
    def extract_technical_terms(self, content):
        """Extract technical terms from content."""
        technical_patterns = [
            r'\b(?:API|SDK|CLI|JWT|OAuth|HTTP|HTTPS|REST|GraphQL|JSON|XML|YAML|SQL|NoSQL)\b',
            r'\b(?:Docker|Kubernetes|AWS|GCP|Azure|GitHub|GitLab|CI/CD)\b',
            r'\b(?:Python|JavaScript|TypeScript|Java|C\+\+|Rust|Go|Ruby|PHP)\b',
            r'\b(?:React|Vue|Angular|Node\.js|Express|Django|Flask|FastAPI)\b',
            r'\b(?:MongoDB|PostgreSQL|MySQL|Redis|Elasticsearch|Kafka)\b',
            r'\b(?:Playwright|Selenium|Puppeteer|Cypress)\b',
            r'\b(?:AI|ML|LLM|NLP|GPT|BERT|Transformer)\b',
            r'\b(?:IoC|DI|MVC|MVP|MVVM|SOLID|DRY|KISS)\b'
        ]
        
        terms = []
        for pattern in technical_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            terms.extend([match.upper() for match in matches])
        
        return terms
    
    def extract_topics(self, content):
        """Extract main topics from content."""
        topic_keywords = {
            "authentication": ["auth", "login", "token", "jwt", "oauth", "credential"],
            "automation": ["playwright", "selenium", "automation", "script", "bot"],
            "architecture": ["architecture", "design", "pattern", "structure", "component"],
            "deployment": ["deploy", "deployment", "docker", "kubernetes", "container"],
            "database": ["database", "sql", "nosql", "mongodb", "postgresql", "redis"],
            "api": ["api", "endpoint", "rest", "graphql", "service", "microservice"],
            "frontend": ["frontend", "ui", "react", "vue", "angular", "javascript"],
            "backend": ["backend", "server", "node", "python", "django", "flask"],
            "testing": ["test", "testing", "unit", "integration", "e2e", "cypress"],
            "security": ["security", "encryption", "ssl", "tls", "vulnerability"],
            "performance": ["performance", "optimization", "cache", "speed", "latency"],
            "monitoring": ["monitoring", "logging", "metrics", "observability", "alert"]
        }
        
        topics = []
        content_lower = content.lower()
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                topics.append(topic)
        
        return topics
    
    def generate_insights(self, analysis):
        """Generate key insights from the analysis."""
        insights = []
        
        # Message distribution insight
        total_msgs = analysis["total_messages"]
        user_msgs = analysis["user_messages"]
        assistant_msgs = analysis["assistant_messages"]
        
        if total_msgs > 0:
            user_ratio = user_msgs / total_msgs
            if user_ratio > 0.6:
                insights.append("User-driven conversation with many questions")
            elif user_ratio < 0.3:
                insights.append("Assistant-heavy conversation with detailed responses")
            else:
                insights.append("Balanced conversation between user and assistant")
        
        # Technical complexity insight
        unique_terms = len(analysis["unique_technical_terms"])
        if unique_terms > 10:
            insights.append("Highly technical conversation with diverse technologies")
        elif unique_terms > 5:
            insights.append("Moderately technical discussion")
        else:
            insights.append("General or non-technical conversation")
        
        # Code-heavy insight
        if analysis["code_blocks"] > 5:
            insights.append("Code-heavy conversation with examples and implementations")
        elif analysis["code_blocks"] > 0:
            insights.append("Contains code examples and technical details")
        
        # Question pattern insight
        if analysis["questions_asked"] > 5:
            insights.append("Exploratory conversation with many questions")
        
        # Length insight
        avg_length = analysis.get("avg_message_length", 0)
        if avg_length > 1000:
            insights.append("Detailed conversation with comprehensive responses")
        elif avg_length < 200:
            insights.append("Concise conversation with brief exchanges")
        
        return insights
    
    def analyze_all_conversations(self):
        """Analyze all conversation JSON files in the extracts directory."""
        json_files = list(self.extracts_dir.glob("structured_*.json"))
        
        if not json_files:
            print("❌ No structured conversation files found")
            return None
        
        all_analyses = []
        
        for json_file in json_files:
            print(f"📊 Analyzing: {json_file.name}")
            analysis = self.analyze_conversation(json_file)
            all_analyses.append(analysis)
        
        # Generate summary report
        summary = self.generate_summary_report(all_analyses)
        
        # Save analysis results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        analysis_file = self.extracts_dir / f"conversation_analysis_{timestamp}.json"
        
        with open(analysis_file, 'w', encoding='utf-8') as f:
            json.dump({
                "summary": summary,
                "individual_analyses": all_analyses,
                "generated_at": datetime.now().isoformat()
            }, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Analysis saved to: {analysis_file}")
        
        return summary, all_analyses
    
    def generate_summary_report(self, analyses):
        """Generate a summary report from all analyses."""
        if not analyses:
            return {}
        
        total_conversations = len(analyses)
        total_messages = sum(a["total_messages"] for a in analyses)
        total_user_messages = sum(a["user_messages"] for a in analyses)
        total_assistant_messages = sum(a["assistant_messages"] for a in analyses)
        
        all_technical_terms = []
        all_topics = []
        all_insights = []
        
        for analysis in analyses:
            all_technical_terms.extend(analysis["unique_technical_terms"])
            all_topics.extend(analysis["unique_topics"])
            all_insights.extend(analysis["key_insights"])
        
        # Count frequencies
        term_frequency = Counter(all_technical_terms)
        topic_frequency = Counter(all_topics)
        insight_frequency = Counter(all_insights)
        
        summary = {
            "total_conversations": total_conversations,
            "total_messages": total_messages,
            "total_user_messages": total_user_messages,
            "total_assistant_messages": total_assistant_messages,
            "avg_messages_per_conversation": total_messages / total_conversations if total_conversations > 0 else 0,
            "most_common_technical_terms": term_frequency.most_common(10),
            "most_common_topics": topic_frequency.most_common(10),
            "most_common_insights": insight_frequency.most_common(5),
            "conversation_titles": [a["title"] for a in analyses]
        }
        
        return summary
    
    def print_summary_report(self, summary):
        """Print a formatted summary report."""
        print("\n" + "="*80)
        print("📊 CONVERSATION ANALYSIS SUMMARY")
        print("="*80)
        
        print(f"📈 Total Conversations: {summary['total_conversations']}")
        print(f"💬 Total Messages: {summary['total_messages']}")
        print(f"👤 User Messages: {summary['total_user_messages']}")
        print(f"🤖 Assistant Messages: {summary['total_assistant_messages']}")
        print(f"📊 Avg Messages/Conversation: {summary['avg_messages_per_conversation']:.1f}")
        
        print(f"\n🔧 Most Common Technical Terms:")
        for term, count in summary['most_common_technical_terms']:
            print(f"  • {term}: {count}")
        
        print(f"\n📋 Most Common Topics:")
        for topic, count in summary['most_common_topics']:
            print(f"  • {topic}: {count}")
        
        print(f"\n💡 Most Common Insights:")
        for insight, count in summary['most_common_insights']:
            print(f"  • {insight}: {count}")
        
        print(f"\n📚 Conversations Analyzed:")
        for title in summary['conversation_titles']:
            print(f"  • {title}")
        
        print("="*80)

if __name__ == "__main__":
    analyzer = ConversationAnalyzer()
    summary, analyses = analyzer.analyze_all_conversations()
    
    if summary:
        analyzer.print_summary_report(summary)
