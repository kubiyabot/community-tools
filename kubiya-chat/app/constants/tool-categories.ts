import { 
  Database, 
  Shield, 
  Cloud, 
  Code2, 
  LineChart, 
  Workflow, 
  Network, 
  Bot,
  Boxes,
  Microscope,
  Wrench,
  Users
} from 'lucide-react';
import type { CategoryInfo } from '../types/tools';

export const toolCategories: CategoryInfo[] = [
  {
    id: 'data-engineering',
    name: 'Data Engineering',
    icon: Database,
    description: 'Tools for ETL, data pipelines, and data infrastructure',
    matcher: (tool) => {
      const keywords = ['data', 'etl', 'pipeline', 'warehouse', 'lake', 'analytics'];
      return keywords.some(k => 
        tool.name.toLowerCase().includes(k) || 
        tool.description.toLowerCase().includes(k)
      );
    }
  },
  {
    id: 'security',
    name: 'Security & Compliance',
    icon: Shield,
    description: 'Security scanning, compliance checks, and vulnerability management',
    matcher: (tool) => {
      const keywords = ['security', 'compliance', 'scan', 'vulnerability', 'audit', 'soc'];
      return keywords.some(k => 
        tool.name.toLowerCase().includes(k) || 
        tool.description.toLowerCase().includes(k)
      );
    }
  },
  {
    id: 'cloud-ops',
    name: 'Cloud Operations',
    icon: Cloud,
    description: 'Cloud infrastructure management and optimization',
    matcher: (tool) => {
      const keywords = ['aws', 'azure', 'gcp', 'cloud', 'kubernetes', 'k8s'];
      return keywords.some(k => 
        tool.name.toLowerCase().includes(k) || 
        tool.description.toLowerCase().includes(k)
      );
    }
  },
  {
    id: 'development',
    name: 'Development Tools',
    icon: Code2,
    description: 'Code analysis, testing, and development workflows',
    matcher: (tool) => {
      const keywords = ['code', 'test', 'ci', 'cd', 'git', 'development'];
      return keywords.some(k => 
        tool.name.toLowerCase().includes(k) || 
        tool.description.toLowerCase().includes(k)
      );
    }
  },
  {
    id: 'monitoring',
    name: 'Monitoring & Observability',
    icon: LineChart,
    description: 'System monitoring, logging, and observability tools',
    matcher: (tool) => {
      const keywords = ['monitor', 'logging', 'metrics', 'trace', 'observe'];
      return keywords.some(k => 
        tool.name.toLowerCase().includes(k) || 
        tool.description.toLowerCase().includes(k)
      );
    }
  },
  {
    id: 'automation',
    name: 'Automation & Workflows',
    icon: Workflow,
    description: 'Process automation and workflow orchestration',
    matcher: (tool) => {
      const keywords = ['automate', 'workflow', 'orchestration', 'pipeline'];
      return keywords.some(k => 
        tool.name.toLowerCase().includes(k) || 
        tool.description.toLowerCase().includes(k)
      );
    }
  },
  {
    id: 'platform-engineering',
    name: 'Platform Engineering',
    icon: Boxes,
    description: 'Internal developer platforms and infrastructure automation',
    matcher: (tool) => {
      const keywords = ['platform', 'infrastructure', 'devops', 'deployment'];
      return keywords.some(k => 
        tool.name.toLowerCase().includes(k) || 
        tool.description.toLowerCase().includes(k)
      );
    }
  },
  {
    id: 'networking',
    name: 'Networking & Connectivity',
    icon: Network,
    description: 'Network management and connectivity tools',
    matcher: (tool) => {
      const keywords = ['network', 'dns', 'proxy', 'connectivity', 'vpn'];
      return keywords.some(k => 
        tool.name.toLowerCase().includes(k) || 
        tool.description.toLowerCase().includes(k)
      );
    }
  },
  {
    id: 'ai-ml',
    name: 'AI & Machine Learning',
    icon: Bot,
    description: 'AI/ML operations and model management',
    matcher: (tool) => {
      const keywords = ['ai', 'ml', 'model', 'inference', 'training'];
      return keywords.some(k => 
        tool.name.toLowerCase().includes(k) || 
        tool.description.toLowerCase().includes(k)
      );
    }
  },
  {
    id: 'testing-quality',
    name: 'Testing & Quality',
    icon: Microscope,
    description: 'Testing automation and quality assurance',
    matcher: (tool) => {
      const keywords = ['test', 'quality', 'qa', 'assertion', 'validation'];
      return keywords.some(k => 
        tool.name.toLowerCase().includes(k) || 
        tool.description.toLowerCase().includes(k)
      );
    }
  },
  {
    id: 'maintenance',
    name: 'Maintenance & Operations',
    icon: Wrench,
    description: 'System maintenance and operational tools',
    matcher: (tool) => {
      const keywords = ['maintenance', 'backup', 'restore', 'operation'];
      return keywords.some(k => 
        tool.name.toLowerCase().includes(k) || 
        tool.description.toLowerCase().includes(k)
      );
    }
  },
  {
    id: 'collaboration',
    name: 'Collaboration & Teams',
    icon: Users,
    description: 'Team collaboration and communication tools',
    matcher: (tool) => {
      const keywords = ['collaboration', 'team', 'chat', 'notification'];
      return keywords.some(k => 
        tool.name.toLowerCase().includes(k) || 
        tool.description.toLowerCase().includes(k)
      );
    }
  }
]; 