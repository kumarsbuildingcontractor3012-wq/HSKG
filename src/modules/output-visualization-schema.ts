import { ImageAnalysisResult, DesignElementMapping } from './ocr-vision-module';

export interface ReviewerOutput {
  projectMetadata: ProjectMetadata;
  summary: ExecutiveSummary;
  designElements: DesignElementReport[];
  mappings: MappingReport[];
  patterns: PatternAnalysis[];
  semanticContributions: SemanticContributionReport;
  twinArchitecture: TwinArchitectureVisualization;
  recommendations: string[];
  exportTimestamp: Date;
}

export interface ProjectMetadata {
  projectName: string;
  totalImagesAnalyzed: number;
  analysisStartDate: Date;
  analysisEndDate: Date;
  version: string;
}

export interface ExecutiveSummary {
  totalDesignElementsExtracted: number;
  conceptsIdentified: string[];
  keyFindings: string[];
  userInteractionPoints: number;
}

export interface DesignElementReport {
  elementId: string;
  sourceImage: string;
  type: string;
  description: string;
  confidence: number;
  visualReference?: string; // Path to extracted visualization
  semanticMeaning: string;
}

export interface MappingReport {
  mappingId: string;
  designElement: string;
  userDataConnection: UserDataLink[];
  relationshipType: string;
  twinRole: string;
}

export interface UserDataLink {
  dataPointId: string;
  dataType: string;
  connectionStrength: 'strong' | 'medium' | 'weak';
  explanation: string;
}

export interface PatternAnalysis {
  patternId: string;
  name: string;
  frequency: number;
  relatedDesignElements: string[];
  userBehaviorCorrelation?: string;
  twinRelevance: string;
}

export interface SemanticContributionReport {
  [elementType: string]: {
    role: string;
    contribution: string;
    examples: string[];
    impactOnTwin: string;
  };
}

export interface TwinArchitectureVisualization {
  digitalTwinRepresentation: string;
  userInteractionFlows: InteractionFlow[];
  feedbackLoops: FeedbackLoop[];
  validationPoints: ValidationPoint[];
}

export interface InteractionFlow {
  flowId: string;
  userAction: string;
  designElementsInvolved: string[];
  twinStateChange: string;
}

export interface FeedbackLoop {
  loopId: string;
  source: string;
  target: string;
  type: 'user-to-system' | 'system-to-user' | 'bidirectional';
  frequency: string;
}

export interface ValidationPoint {
  pointId: string;
  criterion: string;
  designElementsInvolved: string[];
  successMetric: string;
}

export class OutputVisualizationBuilder {
  buildReviewerOutput(
    metadata: ProjectMetadata,
    analysisResults: ImageAnalysisResult[],
    mappings: DesignElementMapping[]
  ): ReviewerOutput {
    return {
      projectMetadata: metadata,
      summary: this.buildExecutiveSummary(analysisResults),
      designElements: this.buildDesignElementReports(analysisResults),
      mappings: this.buildMappingReports(mappings),
      patterns: this.extractPatterns(analysisResults),
      semanticContributions: this.buildSemanticContributions(analysisResults),
      twinArchitecture: this.buildTwinArchitecture(mappings),
      recommendations: this.generateRecommendations(analysisResults, mappings),
      exportTimestamp: new Date(),
    };
  }

  private buildExecutiveSummary(results: ImageAnalysisResult[]): ExecutiveSummary {
    const allConcepts = new Set<string>();
    const totalElements = results.reduce((sum, r) => sum + r.designElements.length, 0);

    results.forEach((r) => r.concepts.forEach((c) => allConcepts.add(c)));

    return {
      totalDesignElementsExtracted: totalElements,
      conceptsIdentified: Array.from(allConcepts),
      keyFindings: ['Multi-layer design architecture identified', 'Strong user-system coupling detected'],
      userInteractionPoints: results.length,
    };
  }

  private buildDesignElementReports(results: ImageAnalysisResult[]): DesignElementReport[] {
    const reports: DesignElementReport[] = [];

    results.forEach((result) => {
      result.designElements.forEach((element) => {
        reports.push({
          elementId: element.id,
          sourceImage: result.imageId,
          type: element.type,
          description: element.description,
          confidence: element.confidence,
          semanticMeaning: this.deriveSemanticMeaning(element),
        });
      });
    });

    return reports;
  }

  private buildMappingReports(mappings: DesignElementMapping[]): MappingReport[] {
    return mappings.map((m) => ({
      mappingId: `map_${m.designElementId}`,
      designElement: m.designElementId,
      userDataConnection: m.userDataReferences.map((ref) => ({
        dataPointId: ref,
        dataType: 'user_interaction',
        connectionStrength: 'medium',
        explanation: `Mapped connection between design element and user data: ${ref}`,
      })),
      relationshipType: m.semanticRole,
      twinRole: m.twinContribution,
    }));
  }

  private extractPatterns(results: ImageAnalysisResult[]): PatternAnalysis[] {
    const patterns: PatternAnalysis[] = [];

    results.forEach((result) => {
      result.concepts.forEach((concept) => {
        const existingPattern = patterns.find((p) => p.name === concept);
        if (existingPattern) {
          existingPattern.frequency++;
        } else {
          patterns.push({
            patternId: `pattern_${concept}_${Date.now()}`,
            name: concept,
            frequency: 1,
            relatedDesignElements: result.designElements.map((e) => e.id),
            twinRelevance: `Contributes to ${concept} aspect of digital twin`,
          });
        }
      });
    });

    return patterns.sort((a, b) => b.frequency - a.frequency);
  }

  private buildSemanticContributions(results: ImageAnalysisResult[]): SemanticContributionReport {
    const contributions: SemanticContributionReport = {};

    results.forEach((result) => {
      result.designElements.forEach((element) => {
        if (!contributions[element.type]) {
          contributions[element.type] = {
            role: `Provides ${element.type} information`,
            contribution: `${element.type} elements structure user understanding`,
            examples: [],
            impactOnTwin: `Influences ${element.type}-related digital twin state`,
          };
        }
        contributions[element.type].examples.push(element.description);
      });
    });

    return contributions;
  }

  private buildTwinArchitecture(mappings: DesignElementMapping[]): TwinArchitectureVisualization {
    return {
      digitalTwinRepresentation: 'Multi-layer twin architecture with user feedback loops',
      userInteractionFlows: mappings
        .filter((m) => m.twinContribution === 'user_interaction')
        .map((m) => ({
          flowId: `flow_${m.designElementId}`,
          userAction: `Interaction with ${m.designElementId}`,
          designElementsInvolved: [m.designElementId],
          twinStateChange: 'Updates twin representation based on user input',
        })),
      feedbackLoops: mappings
        .filter((m) => m.twinContribution === 'feedback_loop')
        .map((m) => ({
          loopId: `loop_${m.designElementId}`,
          source: 'Digital Twin',
          target: 'User Interface',
          type: 'bidirectional',
          frequency: 'continuous',
        })),
      validationPoints: mappings
        .filter((m) => m.twinContribution === 'validation')
        .map((m) => ({
          pointId: `val_${m.designElementId}`,
          criterion: `Validation of ${m.semanticRole}`,
          designElementsInvolved: [m.designElementId],
          successMetric: 'Twin state consistency verified',
        })),
    };
  }

  private deriveSemanticMeaning(element: any): string {
    const meanings: Record<string, string> = {
      text: 'Information presentation',
      shape: 'Structural organization',
      image: 'Visual communication',
      layout: 'Spatial relationship',
      color: 'Semantic encoding',
      typography: 'Hierarchy definition',
    };
    return meanings[element.type] || 'Design contribution';
  }

  private generateRecommendations(results: ImageAnalysisResult[], mappings: DesignElementMapping[]): string[] {
    return [
      'Consider implementing real-time design element validation',
      'Enhance user feedback mechanisms in identified interaction points',
      'Strengthen twin-to-UI communication for critical design elements',
      'Implement pattern-based design consistency checks',
    ];
  }
}
