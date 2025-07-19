#!/usr/bin/env python3
"""
Enhanced Intelligent Router Example
Demonstrates Gemini Code Assist integration with dy-swarm architecture
"""

import asyncio
import re
import yaml
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PrivacyLevel(Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    SENSITIVE = "sensitive"

class RequestType(Enum):
    CODE_REVIEW = "code_review"
    CODE_GENERATION = "code_generation"
    DOCUMENTATION = "documentation"
    SECURITY_ANALYSIS = "security_analysis"

class ComplexityLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"

@dataclass
class CodeRequest:
    content: str
    type: RequestType
    repository: Optional[str] = None
    file_count: int = 1
    line_count: int = 0
    metadata: Dict[str, Any] = None

@dataclass
class RouteDecision:
    target: str
    reason: str
    confidence: float
    cost_estimate: float
    privacy_level: PrivacyLevel
    complexity_level: ComplexityLevel

class PrivacyClassifier:
    """Classifies code content based on privacy and sensitivity"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.sensitive_patterns = self._compile_patterns()
    
    def _compile_patterns(self) -> Dict[str, List[re.Pattern]]:
        """Compile regex patterns for sensitive data detection"""
        patterns = {}
        for category, pattern_list in self.config.get('sensitive_patterns', {}).items():
            patterns[category] = [re.compile(pattern, re.IGNORECASE) for pattern in pattern_list]
        return patterns
    
    async def classify(self, request: CodeRequest) -> PrivacyLevel:
        """Classify the privacy level of the code request"""
        content = request.content.lower()
        
        # Check for sensitive data patterns
        for category, patterns in self.sensitive_patterns.items():
            for pattern in patterns:
                if pattern.search(content):
                    logger.info(f"Sensitive pattern detected: {category}")
                    return PrivacyLevel.SENSITIVE
        
        # Check repository privacy settings
        if request.repository:
            if 'private' in request.repository.lower():
                return PrivacyLevel.INTERNAL
            if any(keyword in request.repository.lower() for keyword in ['confidential', 'secret']):
                return PrivacyLevel.CONFIDENTIAL
        
        # Check for proprietary indicators
        proprietary_indicators = ['internal', 'proprietary', 'confidential', 'company']
        if any(indicator in content for indicator in proprietary_indicators):
            return PrivacyLevel.INTERNAL
        
        return PrivacyLevel.PUBLIC

class ComplexityAnalyzer:
    """Analyzes code complexity to determine appropriate routing"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    async def analyze(self, request: CodeRequest) -> ComplexityLevel:
        """Analyze the complexity of the code request"""
        
        # Simple heuristics for complexity analysis
        complexity_score = 0
        
        # File count factor
        if request.file_count > 10:
            complexity_score += 3
        elif request.file_count > 5:
            complexity_score += 2
        elif request.file_count > 1:
            complexity_score += 1
        
        # Line count factor
        if request.line_count > 1000:
            complexity_score += 3
        elif request.line_count > 500:
            complexity_score += 2
        elif request.line_count > 100:
            complexity_score += 1
        
        # Content complexity indicators
        content = request.content.lower()
        complex_patterns = [
            'algorithm', 'optimization', 'performance', 'concurrency',
            'threading', 'async', 'database', 'security', 'encryption',
            'machine learning', 'ai', 'neural network'
        ]
        
        for pattern in complex_patterns:
            if pattern in content:
                complexity_score += 1
        
        # Map score to complexity level
        if complexity_score >= 6:
            return ComplexityLevel.VERY_HIGH
        elif complexity_score >= 4:
            return ComplexityLevel.HIGH
        elif complexity_score >= 2:
            return ComplexityLevel.MEDIUM
        else:
            return ComplexityLevel.LOW

class CostOptimizer:
    """Optimizes routing decisions based on cost considerations"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.cost_estimates = config.get('cost_estimates', {})
        self.daily_limits = config.get('daily_limits', {})
        self.current_usage = {}  # In production, this would be persistent
    
    async def estimate_cost(self, target: str, request: CodeRequest) -> float:
        """Estimate the cost of routing to a specific target"""
        base_cost = self.cost_estimates.get(target, 0.001)
        
        # Adjust cost based on request complexity
        complexity_multiplier = {
            ComplexityLevel.LOW: 1.0,
            ComplexityLevel.MEDIUM: 1.5,
            ComplexityLevel.HIGH: 2.0,
            ComplexityLevel.VERY_HIGH: 3.0
        }
        
        # For this example, assume medium complexity
        return base_cost * complexity_multiplier.get(ComplexityLevel.MEDIUM, 1.0)
    
    async def check_budget_limits(self, target: str) -> bool:
        """Check if the target is within budget limits"""
        daily_limit = self.daily_limits.get(target, float('inf'))
        current_usage = self.current_usage.get(target, 0)
        
        return current_usage < daily_limit

class EnhancedIntelligentRouter:
    """Enhanced router with Gemini Code Assist integration"""
    
    def __init__(self, config_path: str = "config/gemini_code_assist_config.yaml"):
        self.config = self._load_config(config_path)
        self.privacy_classifier = PrivacyClassifier(self.config.get('privacy', {}))
        self.complexity_analyzer = ComplexityAnalyzer(self.config.get('intelligent_router', {}))
        self.cost_optimizer = CostOptimizer(self.config.get('cost_optimization', {}))
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            logger.warning(f"Config file {config_path} not found, using defaults")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Return default configuration"""
        return {
            'privacy': {
                'sensitive_patterns': {
                    'api_keys': [r'api[_-]?key'],
                    'passwords': [r'password'],
                    'secrets': [r'secret'],
                    'tokens': [r'token']
                }
            },
            'cost_optimization': {
                'cost_estimates': {
                    'gemini_code_assist': 0.002,
                    'gemini_pro': 0.005,
                    'local_llama': 0.0,
                    'featherless_ai': 0.001
                },
                'daily_limits': {
                    'gemini_code_assist': 800,
                    'gemini_pro': 200,
                    'local_llama': 1000,
                    'featherless_ai': 500
                }
            }
        }
    
    async def route_request(self, request: CodeRequest) -> RouteDecision:
        """Main routing logic with enhanced intelligence"""
        
        # Step 1: Privacy classification
        privacy_level = await self.privacy_classifier.classify(request)
        logger.info(f"Privacy level: {privacy_level}")
        
        # Step 2: Complexity analysis
        complexity_level = await self.complexity_analyzer.analyze(request)
        logger.info(f"Complexity level: {complexity_level}")
        
        # Step 3: Privacy-first routing
        if privacy_level in [PrivacyLevel.SENSITIVE, PrivacyLevel.CONFIDENTIAL]:
            cost = await self.cost_optimizer.estimate_cost('local_llama', request)
            return RouteDecision(
                target='local_llama',
                reason='privacy_required',
                confidence=1.0,
                cost_estimate=cost,
                privacy_level=privacy_level,
                complexity_level=complexity_level
            )
        
        # Step 4: Request type and complexity-based routing
        target = await self._determine_optimal_target(request, complexity_level, privacy_level)
        
        # Step 5: Budget and availability check
        if not await self.cost_optimizer.check_budget_limits(target):
            target = await self._get_fallback_target(target, privacy_level)
        
        # Step 6: Calculate final decision
        cost = await self.cost_optimizer.estimate_cost(target, request)
        confidence = await self._calculate_confidence(request, target, complexity_level)
        reason = await self._get_routing_reason(request, target, complexity_level)
        
        return RouteDecision(
            target=target,
            reason=reason,
            confidence=confidence,
            cost_estimate=cost,
            privacy_level=privacy_level,
            complexity_level=complexity_level
        )
    
    async def _determine_optimal_target(self, request: CodeRequest, complexity: ComplexityLevel, privacy: PrivacyLevel) -> str:
        """Determine the optimal target based on request characteristics"""
        
        if request.type == RequestType.CODE_REVIEW:
            if complexity in [ComplexityLevel.LOW, ComplexityLevel.MEDIUM]:
                return 'gemini_code_assist'
            else:
                return 'gemini_pro'
        
        elif request.type == RequestType.CODE_GENERATION:
            return 'gemini_code_assist'
        
        elif request.type == RequestType.SECURITY_ANALYSIS:
            if privacy == PrivacyLevel.PUBLIC:
                return 'gemini_code_assist'
            else:
                return 'local_llama'
        
        elif request.type == RequestType.DOCUMENTATION:
            return 'gemini_code_assist'
        
        # Default fallback
        return 'gemini_pro'
    
    async def _get_fallback_target(self, original_target: str, privacy_level: PrivacyLevel) -> str:
        """Get fallback target when original is unavailable"""
        fallback_map = {
            'gemini_code_assist': 'gemini_pro',
            'gemini_pro': 'local_llama' if privacy_level != PrivacyLevel.PUBLIC else 'featherless_ai',
            'featherless_ai': 'local_llama',
            'local_llama': 'local_llama'  # Always available
        }
        
        return fallback_map.get(original_target, 'local_llama')
    
    async def _calculate_confidence(self, request: CodeRequest, target: str, complexity: ComplexityLevel) -> float:
        """Calculate confidence score for the routing decision"""
        base_confidence = 0.8
        
        # Adjust based on target-complexity match
        if target == 'gemini_code_assist' and complexity in [ComplexityLevel.LOW, ComplexityLevel.MEDIUM]:
            base_confidence += 0.1
        elif target == 'gemini_pro' and complexity in [ComplexityLevel.HIGH, ComplexityLevel.VERY_HIGH]:
            base_confidence += 0.1
        elif target == 'local_llama':
            base_confidence += 0.05  # Always reliable for privacy
        
        return min(base_confidence, 1.0)
    
    async def _get_routing_reason(self, request: CodeRequest, target: str, complexity: ComplexityLevel) -> str:
        """Get human-readable reason for routing decision"""
        if target == 'local_llama':
            return 'privacy_compliance'
        elif target == 'gemini_code_assist':
            if complexity == ComplexityLevel.LOW:
                return 'simple_code_assistance'
            else:
                return 'standard_code_review'
        elif target == 'gemini_pro':
            return 'complex_analysis_required'
        elif target == 'featherless_ai':
            return 'cost_optimization'
        else:
            return 'default_routing'

# Example usage and demonstration
async def demonstrate_enhanced_routing():
    """Demonstrate the enhanced routing capabilities"""
    
    router = EnhancedIntelligentRouter()
    
    # Test cases
    test_cases = [
        CodeRequest(
            content="def hello_world(): return 'Hello, World!'",
            type=RequestType.CODE_REVIEW,
            repository="public-repo",
            file_count=1,
            line_count=10
        ),
        CodeRequest(
            content="API_KEY = 'secret123'\npassword = 'admin123'",
            type=RequestType.SECURITY_ANALYSIS,
            repository="private-repo",
            file_count=1,
            line_count=5
        ),
        CodeRequest(
            content="Complex machine learning algorithm with neural networks and optimization",
            type=RequestType.CODE_REVIEW,
            repository="ml-project",
            file_count=15,
            line_count=2000
        ),
        CodeRequest(
            content="Generate a simple REST API endpoint",
            type=RequestType.CODE_GENERATION,
            repository="api-project",
            file_count=1,
            line_count=50
        )
    ]
    
    print("🚀 Enhanced Intelligent Router Demonstration")
    print("=" * 60)
    
    for i, request in enumerate(test_cases, 1):
        print(f"\n📋 Test Case {i}:")
        print(f"   Content: {request.content[:50]}...")
        print(f"   Type: {request.type.value}")
        print(f"   Repository: {request.repository}")
        print(f"   Files: {request.file_count}, Lines: {request.line_count}")
        
        decision = await router.route_request(request)
        
        print(f"\n🎯 Routing Decision:")
        print(f"   Target: {decision.target}")
        print(f"   Reason: {decision.reason}")
        print(f"   Confidence: {decision.confidence:.2f}")
        print(f"   Cost Estimate: ${decision.cost_estimate:.4f}")
        print(f"   Privacy Level: {decision.privacy_level.value}")
        print(f"   Complexity: {decision.complexity_level.value}")
        print("-" * 60)

if __name__ == "__main__":
    asyncio.run(demonstrate_enhanced_routing())

