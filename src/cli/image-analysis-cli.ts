import * as path from 'path';
import { BatchImageProcessor } from '../modules/batch-image-processor';

export async function analyzeDesignImages(imageDir: string, outputDir?: string): Promise<void> {
  const processor = new BatchImageProcessor();

  const imageDirectory = path.resolve(imageDir);
  const reportOutputDir = path.resolve(outputDir || './design-analysis-reports');

  console.log('=== Design Concept Extraction & Analysis ===');
  console.log(`Input Directory: ${imageDirectory}`);
  console.log(`Output Directory: ${reportOutputDir}`);
  console.log('');

  try {
    await processor.processBatch(imageDirectory, reportOutputDir);
    console.log('\n✅ Analysis completed successfully!');
    console.log(`Reports generated in: ${reportOutputDir}`);
  } catch (error) {
    console.error('❌ Analysis failed:', error);
    process.exit(1);
  }
}

// CLI entry point
if (require.main === module) {
  const args = process.argv.slice(2);
  const imageDir = args[0] || './design-images';
  const outputDir = args[1];

  analyzeDesignImages(imageDir, outputDir).catch(console.error);
}
