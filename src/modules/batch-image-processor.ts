import * as fs from 'fs';
import * as path from 'path';
import { OCRVisionModule, ImageAnalysisResult, DesignElementMapping } from './ocr-vision-module';
import { OutputVisualizationBuilder, ProjectMetadata } from './output-visualization-schema';

export class BatchImageProcessor {
  private ocrModule: OCRVisionModule;
  private visualizationBuilder: OutputVisualizationBuilder;
  private processedCount: number = 0;

  constructor() {
    this.ocrModule = new OCRVisionModule();
    this.visualizationBuilder = new OutputVisualizationBuilder();
  }

  async processBatch(imageDirectory: string, outputDir: string): Promise<void> {
    console.log(`Starting batch processing for images in: ${imageDirectory}`);

    const imageFiles = this.getImageFiles(imageDirectory);
    console.log(`Found ${imageFiles.length} images to process`);

    const analysisResults: ImageAnalysisResult[] = [];

    for (const imagePath of imageFiles) {
      try {
        const result = await this.ocrModule.extractDesignConcepts(imagePath);
        analysisResults.push(result);
        this.processedCount++;

        // Map design elements to user data (requires user data source)
        this.mapElementsToUserData(result);

        if (this.processedCount % 50 === 0) {
          console.log(`Processed ${this.processedCount}/${imageFiles.length} images`);
        }
      } catch (error) {
        console.error(`Failed to process ${imagePath}:`, error);
      }
    }

    // Generate output report
    await this.generateOutputReport(analysisResults, outputDir);
  }

  private getImageFiles(directory: string): string[] {
    const supportedFormats = ['.png', '.jpg', '.jpeg', '.webp', '.bmp', '.gif'];
    const files: string[] = [];

    const traverse = (dir: string) => {
      try {
        const entries = fs.readdirSync(dir, { withFileTypes: true });
        entries.forEach((entry) => {
          const fullPath = path.join(dir, entry.name);
          if (entry.isDirectory()) {
            traverse(fullPath);
          } else if (supportedFormats.includes(path.extname(entry.name).toLowerCase())) {
            files.push(fullPath);
          }
        });
      } catch (error) {
        console.error(`Error reading directory ${dir}:`, error);
      }
    };

    traverse(directory);
    return files;
  }

  private mapElementsToUserData(result: ImageAnalysisResult): void {
    result.designElements.forEach((element) => {
      // Example mapping - adapt based on actual user data source
      this.ocrModule.mapDesignElementToUserData(
        element.id,
        result.imageId,
        [`user_session_${result.timestamp.toISOString()}`],
        `Extracted from: ${element.type}`,
        'digital_twin'
      );
    });
  }

  private async generateOutputReport(results: ImageAnalysisResult[], outputDir: string): Promise<void> {
    const metadata: ProjectMetadata = {
      projectName: 'Design Concept Extraction - 819 Images',
      totalImagesAnalyzed: results.length,
      analysisStartDate: new Date(),
      analysisEndDate: new Date(),
      version: '1.0.0',
    };

    const mappings = this.ocrModule.getMappings();
    const reviewerOutput = this.visualizationBuilder.buildReviewerOutput(metadata, results, mappings);

    // Ensure output directory exists
    if (!fs.existsSync(outputDir)) {
      fs.mkdirSync(outputDir, { recursive: true });
    }

    // Write JSON report
    const jsonPath = path.join(outputDir, 'analysis-report.json');
    fs.writeFileSync(jsonPath, JSON.stringify(reviewerOutput, null, 2));
    console.log(`Report written to: ${jsonPath}`);

    // Write HTML report for visualization
    const htmlPath = path.join(outputDir, 'analysis-report.html');
    fs.writeFileSync(htmlPath, this.generateHTMLReport(reviewerOutput));
    console.log(`HTML report written to: ${htmlPath}`);

    // Write CSV for design elements
    const csvPath = path.join(outputDir, 'design-elements.csv');
    fs.writeFileSync(csvPath, this.generateCSVReport(reviewerOutput.designElements));
    console.log(`CSV report written to: ${csvPath}`);
  }

  private generateHTMLReport(output: any): string {
    return `
      <!DOCTYPE html>
      <html>
      <head>
        <title>Design Analysis Report</title>
        <style>
          body { font-family: Arial; margin: 20px; background: #f5f5f5; }
          .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }
          h1 { color: #333; border-bottom: 2px solid #007bff; }
          .summary { background: #e7f3ff; padding: 15px; border-radius: 5px; margin: 10px 0; }
          table { width: 100%; border-collapse: collapse; margin: 20px 0; }
          th { background: #007bff; color: white; padding: 10px; text-align: left; }
          td { padding: 10px; border-bottom: 1px solid #ddd; }
          .element-section { margin: 20px 0; padding: 15px; background: #f9f9f9; border-left: 4px solid #007bff; }
        </style>
      </head>
      <body>
        <div class="container">
          <h1>🎨 Design Concept Extraction Analysis Report</h1>
          <div class="summary">
            <strong>Total Images Analyzed:</strong> ${output.projectMetadata.totalImagesAnalyzed}<br>
            <strong>Design Elements Extracted:</strong> ${output.summary.totalDesignElementsExtracted}<br>
            <strong>Concepts Identified:</strong> ${output.summary.conceptsIdentified.join(', ')}<br>
            <strong>Analysis Date:</strong> ${output.exportTimestamp}
          </div>

          <h2>Design Elements Found</h2>
          <table>
            <tr><th>Element ID</th><th>Type</th><th>Description</th><th>Confidence</th><th>Semantic Meaning</th></tr>
            ${output.designElements.map((el: any) => `<tr><td>${el.elementId}</td><td>${el.type}</td><td>${el.description}</td><td>${(el.confidence * 100).toFixed(1)}%</td><td>${el.semanticMeaning}</td></tr>`).join('')}
          </table>

          <h2>Key Patterns Identified</h2>
          <div>
            ${output.patterns.map((p: any) => `<div class="element-section"><strong>${p.name}</strong> (Frequency: ${p.frequency})<br>${p.twinRelevance}</div>`).join('')}
          </div>

          <h2>Recommendations</h2>
          <ul>
            ${output.recommendations.map((r: string) => `<li>${r}</li>`).join('')}
          </ul>
        </div>
      </body>
      </html>
    `;
  }

  private generateCSVReport(elements: any[]): string {
    const headers = ['Element ID', 'Source Image', 'Type', 'Description', 'Confidence', 'Semantic Meaning'];
    const rows = elements.map((el) => [
      el.elementId,
      el.sourceImage,
      el.type,
      el.description,
      el.confidence,
      el.semanticMeaning,
    ]);

    const csv = [
      headers.join(','),
      ...rows.map((row) => row.map((cell) => `"${cell}"`).join(',')),
    ].join('\n');

    return csv;
  }
}