/**
 * 
 */
package ee.olegus.cpr;

import java.io.File;
import java.io.IOException;
import java.util.List;

import javax.xml.transform.OutputKeys;
import javax.xml.transform.Transformer;
import javax.xml.transform.TransformerConfigurationException;
import javax.xml.transform.sax.SAXTransformerFactory;
import javax.xml.transform.sax.TransformerHandler;
import javax.xml.transform.stream.StreamResult;

import org.apache.commons.cli.CommandLine;
import org.apache.commons.cli.GnuParser;
import org.apache.commons.cli.HelpFormatter;
import org.apache.commons.cli.Option;
import org.apache.commons.cli.OptionBuilder;
import org.apache.commons.cli.Options;
import org.apache.commons.cli.ParseException;
import org.apache.log4j.BasicConfigurator;
import org.apache.log4j.Level;
import org.apache.log4j.LogManager;
import org.apache.log4j.Logger;
import org.xml.sax.SAXException;

import ee.olegus.fortran.Parser;

/**
 * Main class.
 * 
 * @author olegus
 *
 */
@SuppressWarnings("static-access")
public class FortranCPR {
	private static final Logger LOG = LogManager.getLogger(FortranCPR.class);
	
	private static final String INDIR = "indir";
	private static final String OUTDIR = "outdir";
	
	private static Options options = new Options();
	
	static {
		Option option;
		option = new Option("h", "help", false, "show this text");
		options.addOption(option);
		
		option = OptionBuilder.withLongOpt(INDIR).
			withDescription("input directory").
			hasArg().
			withArgName("directory").
			create('I');
		options.addOption(option);

		option = OptionBuilder.withLongOpt(OUTDIR).
		withDescription("output directory").
		hasArg().
		withArgName("directory").
		create('O');
		options.addOption(option);

		option = OptionBuilder.withLongOpt("outxml").
		withDescription("output xml to file").
		hasArg().
		withArgName("xmlfile").
		create('X');
		options.addOption(option);
	}	
	
	/**
	 * @param args
	 * @throws ParseException 
	 */
	public static void main(String[] args) throws ParseException {
		BasicConfigurator.configure();
		LogManager.getRootLogger().setLevel(Level.INFO);
		
		org.apache.commons.cli.Parser optionParser = new GnuParser();
		CommandLine commandLine = optionParser.parse(options, args);
		
		if(commandLine.getArgs().length == 0 || 
				commandLine.hasOption('h') || commandLine.hasOption("help")) {
			new HelpFormatter().printHelp("FortranCPR <options> <Fortran files>", options);
			System.exit(0);
		}

		File inDir = new File(commandLine.getOptionValue('I', ""));
		FortranCPR fortranCPR = new FortranCPR(inDir, commandLine.getArgList(), args);
		
		if(commandLine.hasOption("X")) {
			try {
				String xmlfilename = commandLine.getOptionValue("X");
				File xmlfile = new File(xmlfilename);
				
				fortranCPR.writeXML(xmlfile);
			} catch (SAXException e) {
				throw new RuntimeException(e);
			} catch (TransformerConfigurationException e) {
				throw new RuntimeException(e);
			}
		}
		//analyzer.createReferenceTable();
		//analyzer.analyze();
		//analyzer.generateCode();
		
		//File outDir = new File(commandLine.getOptionValue('O', "generated"));
		//Output output = new Output(outDir, analyzer.getTokenStreams(), analyzer.getStringTemplates());
		//output.writeOut();
	}	
	
	private void writeXML(File xmlfile) throws TransformerConfigurationException, SAXException {
		StreamResult streamResult = new StreamResult(xmlfile);
		SAXTransformerFactory tf = (SAXTransformerFactory) SAXTransformerFactory.newInstance();
		// SAX2.0 ContentHandler.
		TransformerHandler hd = tf.newTransformerHandler();
		Transformer serializer = hd.getTransformer();
		serializer.setOutputProperty(OutputKeys.ENCODING,"UTF-8");
		//serializer.setOutputProperty(OutputKeys.DOCTYPE_SYSTEM,"users.dtd");
		serializer.setOutputProperty(OutputKeys.INDENT,"yes");
		hd.setResult(streamResult);
		hd.startDocument();
		hd.startElement("", "", "ASTCollection", null);
		
		parser.generateXML(hd);
		
		hd.endElement("", "", "ASTCollection");
		hd.endDocument();
	}

	private File inDir;
	private List<String> files;
	private Parser parser;
	
	public FortranCPR(File inDir, List<String> files, String[] args) {
		this.inDir = inDir;
		this.files = files;
		this.parser = new Parser();
		
		LOG.info("Input directory: "+this.inDir);
		
		for(String file: files) {
			try {
				if(file.endsWith("F90"))
					file = preprocess(file);
				parser.feed(this.inDir, file, args);
			} catch (Exception e) {
				LOG.error("Error parsing "+file, e);
				throw new RuntimeException(e);
			}
		}
		
		parser.postProcess();
	}	
	
	private String preprocess(String file) {
		try {
			Process process = Runtime.getRuntime().exec(new String[]{"cpp","-traditional-cpp","-o",file+".f90",
					"-I/home/olegus/uni/master/workspace/doug_trunk/src", file});
			int exitValue = process.waitFor();
			if(exitValue != 0)
				throw new RuntimeException("cpp execution error, return code "+exitValue);
		} catch (IOException e) {
			LOG.error(e);
			throw new RuntimeException(e);
		} catch (InterruptedException e) {
			LOG.error(e);
			throw new RuntimeException(e);
		}
		return file+".f90";
	}
	
	public List<String> getFiles() {
		return files;
	}	
}
