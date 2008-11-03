/**
 * 
 */
package ee.olegus.cpr;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.util.Map;

import org.antlr.stringtemplate.StringTemplate;
import org.antlr.stringtemplate.StringTemplateGroup;
import org.apache.log4j.LogManager;
import org.apache.log4j.Logger;

import fortran.ofp.parser.java.FortranTokenStream;

/**
 * @author olegus
 *
 */
public class Output {
	private static final Logger LOG = LogManager.getLogger(Output.class);
	private Map<String,FortranTokenStream> tokenStreams;
	private Map<String,StringTemplate> stringTemplates;
	private File outDir;
	
	public Output(File outDir, Map<String,FortranTokenStream> tokenStreams, 
			Map<String,StringTemplate> stringTemplates) {
		this.tokenStreams = tokenStreams;
		this.stringTemplates = stringTemplates;
		this.outDir = outDir;
		if(!this.outDir.exists()) {
			this.outDir.mkdir();
		}
		
		LOG.info("Output directory: "+this.outDir);
	}
	
	public void writeOut() throws IOException {
		
		for(String filename: tokenStreams.keySet()) {
			FortranTokenStream stream = tokenStreams.get(filename);
			int index = filename.lastIndexOf('.');
			if(index==-1) index = filename.length();
			String newFilename = filename.substring(0, index)+".cpr"+filename.substring(index);
			
			LOG.info("Writing out "+newFilename);
			File file = new File(outDir, newFilename);
			FileWriter outWriter = new FileWriter(file);
			outWriter.write(stream.toString());
			outWriter.close();
		}
		
		for(String filename: stringTemplates.keySet()) {
			LOG.info("Writing out "+filename);
			
			StringTemplate template = stringTemplates.get(filename);
			File file = new File(outDir, filename);
			FileWriter outWriter = new FileWriter(file);
			outWriter.write(template.toString());
			outWriter.close();
		}

		// write out CPR module
		generateFile("cpr-f9x-file", "cprmodule", "cpr.f90");
		// write out C file
		generateFile("cpr-f9x-cfile", "cprcfile", "cpr_c.c");
		// write out cpr data C file
		generateFile("cpr-f9x-cfile", "cprdatacfile", "cpr_data.c");		
	}

	/**
	 * @throws IOException
	 */
	private void generateFile(String fileName, String templateName, String outFileName) throws IOException {
		StringTemplateGroup group = StringTemplateGroup.loadGroup(fileName);
		
		StringTemplate cprfile_t = group.getInstanceOf(templateName);
		
		LOG.info("Writing out "+outFileName);
		File file = new File(outDir, outFileName);
		FileWriter outWriter = new FileWriter(file);
		outWriter.write(cprfile_t.toString());
		outWriter.close();
	}
}
