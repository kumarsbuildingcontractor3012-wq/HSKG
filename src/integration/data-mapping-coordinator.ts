export interface UserDataPoint {
  id: string;
  type: 'interaction' | 'preference' | 'feedback' | 'behavior' | 'demographic';
  value: any;
  timestamp: Date;
  sourceSystem?: string;
}

export interface DesignUserMapping {
  id: string;
  designElementId: string;
  userDataPointId: string;
  relationshipStrength: number; // 0-1
  mappingType: 'direct' | 'indirect' | 'contextual' | 'inferred';
  evidenceScore: number;
  explanation: string;
  twinRelevance: {
    affects: string[];
    affectedBy: string[];
  };
}

export class DataMappingCoordinator {
  private mappings: DesignUserMapping[] = [];
  private userDataPoints: Map<string, UserDataPoint> = new Map();

  registerUserData(dataPoint: UserDataPoint): void {
    this.userDataPoints.set(dataPoint.id, dataPoint);
  }

  createMapping(
    designElementId: string,
    userDataPointId: string,
    relationshipStrength: number,
    mappingType: DesignUserMapping['mappingType'],
    explanation: string
  ): DesignUserMapping {
    const mapping: DesignUserMapping = {
      id: `map_${Date.now()}_${Math.random()}`,
      designElementId,
      userDataPointId,
      relationshipStrength,
      mappingType,
      evidenceScore: this.calculateEvidenceScore(designElementId, userDataPointId),
      explanation,
      twinRelevance: {
        affects: [],
        affectedBy: [],
      },
    };

    this.mappings.push(mapping);
    return mapping;
  }

  private calculateEvidenceScore(designElementId: string, userDataPointId: string): number {
    // TODO: Implement scoring based on data analysis
    return Math.random();
  }

  getMappings(): DesignUserMapping[] {
    return this.mappings;
  }

  getMappingsForDesignElement(elementId: string): DesignUserMapping[] {
    return this.mappings.filter((m) => m.designElementId === elementId);
  }

  getMappingsForUserData(dataPointId: string): DesignUserMapping[] {
    return this.mappings.filter((m) => m.userDataPointId === dataPointId);
  }
}
