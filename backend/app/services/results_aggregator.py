"""
Results Aggregator Service - Handles aggregation and storage of analysis results
"""
import json
import os
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
from app.core.llm_provider import llm_provider
from app.agents.supervisor_agent import SupervisorAgent
from app.agents.trend_agent import TrendAgent

class ResultsAggregator:
    """Service for aggregating and managing analysis results"""
    
    def __init__(self, results_dir: str = None):
        self.results_dir = results_dir or os.path.join(os.getcwd(), 'analysis_results')
        self.supervisor = SupervisorAgent(llm_provider)
        self.trend_agent = TrendAgent(llm_provider)
        
        # Ensure results directory exists
        os.makedirs(self.results_dir, exist_ok=True)
    
    async def run_full_analysis(self, repo_path: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Run complete analysis and aggregate results"""
        try:
            # Run the main analysis
            analysis_results = await self.supervisor.run_full_analysis(repo_path, context)
            
            if not analysis_results.get('success'):
                return analysis_results
            
            # Add trend analysis
            trend_context = {
                'current_analysis': analysis_results,
                **(context or {})
            }
            
            trend_results = await self.trend_agent.analyze(repo_path, trend_context)
            analysis_results['trend_analysis'] = trend_results
            
            # Store results
            result_id = self._store_results(repo_path, analysis_results)
            analysis_results['result_id'] = result_id
            
            return analysis_results
        
        except Exception as e:
            return {
                'success': False,
                'error': f"Analysis failed: {str(e)}",
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def run_selective_analysis(self, repo_path: str, agent_names: List[str], 
                                   context: Optional[Dict] = None) -> Dict[str, Any]:
        """Run analysis with selected agents only"""
        try:
            analysis_results = await self.supervisor.run_selective_analysis(
                repo_path, agent_names, context
            )
            
            if analysis_results.get('success'):
                result_id = self._store_results(repo_path, analysis_results)
                analysis_results['result_id'] = result_id
            
            return analysis_results
        
        except Exception as e:
            return {
                'success': False,
                'error': f"Selective analysis failed: {str(e)}",
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def _store_results(self, repo_path: str, results: Dict[str, Any]) -> str:
        """Store analysis results to file"""
        try:
            # Generate unique result ID
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            repo_name = Path(repo_path).name
            result_id = f"{repo_name}_{timestamp}"
            
            # Create result file
            result_file = os.path.join(self.results_dir, f"{result_id}.json")
            
            # Prepare results for storage
            storage_results = {
                'result_id': result_id,
                'repo_path': repo_path,
                'stored_at': datetime.utcnow().isoformat(),
                **results
            }
            
            with open(result_file, 'w') as f:
                json.dump(storage_results, f, indent=2, default=str)
            
            return result_id
        
        except Exception as e:
            # If storage fails, log error but don't fail the analysis
            print(f"Warning: Failed to store results: {e}")
            return f"unsaved_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    
    def get_results(self, result_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve stored analysis results"""
        try:
            result_file = os.path.join(self.results_dir, f"{result_id}.json")
            
            if not os.path.exists(result_file):
                return None
            
            with open(result_file, 'r') as f:
                return json.load(f)
        
        except Exception as e:
            print(f"Error retrieving results: {e}")
            return None
    
    def list_results(self, repo_path: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """List stored analysis results"""
        try:
            results = []
            
            for filename in os.listdir(self.results_dir):
                if not filename.endswith('.json'):
                    continue
                
                try:
                    filepath = os.path.join(self.results_dir, filename)
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                    
                    # Filter by repo_path if specified
                    if repo_path and data.get('repo_path') != repo_path:
                        continue
                    
                    # Create summary entry
                    results.append({
                        'result_id': data.get('result_id'),
                        'repo_path': data.get('repo_path'),
                        'overall_score': data.get('overall_score'),
                        'timestamp': data.get('analysis_metadata', {}).get('timestamp'),
                        'stored_at': data.get('stored_at'),
                        'success': data.get('success', False),
                        'agents_executed': data.get('agents_executed', []),
                        'total_issues': len(data.get('all_issues', []))
                    })
                
                except (json.JSONDecodeError, KeyError):
                    continue
            
            # Sort by timestamp (newest first) and limit
            results.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            return results[:limit]
        
        except Exception as e:
            print(f"Error listing results: {e}")
            return []
    
    def delete_results(self, result_id: str) -> bool:
        """Delete stored analysis results"""
        try:
            result_file = os.path.join(self.results_dir, f"{result_id}.json")
            
            if os.path.exists(result_file):
                os.remove(result_file)
                return True
            
            return False
        
        except Exception as e:
            print(f"Error deleting results: {e}")
            return False
    
    def get_trend_report(self, repo_path: str, days: int = 30) -> Dict[str, Any]:
        """Get trend analysis report for a repository"""
        return self.trend_agent.get_trend_report(repo_path, days)
    
    def cleanup_old_results(self, days_to_keep: int = 90):
        """Clean up old result files and trend data"""
        try:
            from datetime import timedelta
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            
            deleted_count = 0
            
            for filename in os.listdir(self.results_dir):
                if not filename.endswith('.json'):
                    continue
                
                filepath = os.path.join(self.results_dir, filename)
                
                try:
                    # Check file modification time
                    file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                    
                    if file_time < cutoff_date:
                        os.remove(filepath)
                        deleted_count += 1
                
                except OSError:
                    continue
            
            # Also cleanup trend database
            self.trend_agent.cleanup_old_data(days_to_keep)
            
            print(f"Cleaned up {deleted_count} old result files")
            
        except Exception as e:
            print(f"Error during cleanup: {e}")
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all agents"""
        return self.supervisor.get_agent_status()
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform system health check"""
        try:
            # Check LLM provider
            llm_healthy = await llm_provider.check_health()
            
            # Check results directory
            results_writable = os.access(self.results_dir, os.W_OK)
            
            # Check agent status
            agent_status = self.get_agent_status()
            
            return {
                'healthy': llm_healthy and results_writable,
                'llm_provider': {
                    'status': 'healthy' if llm_healthy else 'unhealthy',
                    'model': llm_provider.model,
                    'base_url': llm_provider.base_url
                },
                'storage': {
                    'status': 'healthy' if results_writable else 'unhealthy',
                    'results_dir': self.results_dir,
                    'writable': results_writable
                },
                'agents': agent_status,
                'timestamp': datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }

# Global instance
results_aggregator = ResultsAggregator()
