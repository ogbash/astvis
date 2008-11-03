/**
 * 
 */
package ee.olegus.fortran;

import java.util.HashMap;
import java.util.Map;

import org.xml.sax.ContentHandler;
import org.xml.sax.SAXException;
import org.xml.sax.helpers.AttributesImpl;

import fortran.ofp.parser.java.FortranTokenStream;
import ee.olegus.fortran.ast.ProgramUnit;
import ee.olegus.fortran.ast.Subprogram;
import ee.olegus.fortran.ast.text.Location;

/**
 * @author olegus
 *
 */
public class FortranFile implements XMLGenerator, ASTVisitable {

	private String filename;
	private Map<String,ProgramUnit> programUnits = new HashMap<String,ProgramUnit>();
	private Map<String,Subprogram> subprograms = new HashMap<String,Subprogram>();
	private FortranTokenStream tokenStream;
	
	public FortranTokenStream getTokenStream() {
		return tokenStream;
	}

	public Map<String, Subprogram> getSubprograms() {
		return subprograms;
	}

	public void setSubprograms(Map<String, Subprogram> subprograms) {
		this.subprograms = subprograms;
	}

	public void setTokenStream(FortranTokenStream tokenStream) {
		this.tokenStream = tokenStream;
	}

	public String getFilename() {
		return filename;
	}

	public void setFilename(String filename) {
		this.filename = filename;
	}

	public Map<String,ProgramUnit> getProgramUnits() {
		return programUnits;
	}

	public void setProgramUnits(Map<String,ProgramUnit> programUnits) {
		this.programUnits = programUnits;
	}

	public FortranFile(String filename) {
		this.filename = filename;
	}

	public void generateXML(ContentHandler handler) throws SAXException {
		Location.tokenStream.set(tokenStream);
		try {
			AttributesImpl attrs = new AttributesImpl();
			attrs.addAttribute("", "", "name", "", filename);
			handler.startElement("", "", "file", attrs);

			for(Subprogram subprogram: subprograms.values())
				subprogram.generateXML(handler);
			for(ProgramUnit unit: programUnits.values())
				unit.generateXML(handler);

			handler.endElement("", "", "file");
		} finally {
			Location.tokenStream.set(null);			
		}
	}

	public Object astWalk(ASTVisitor visitor) {
		for(ProgramUnit unit: programUnits.values()) {
			unit.astWalk(visitor);
		}
		
		return this;
	}

}
