/**
 * 
 */
package ee.olegus.fortran.ast;

import java.util.List;

import org.xml.sax.ContentHandler;
import org.xml.sax.SAXException;
import org.xml.sax.helpers.AttributesImpl;

import ee.olegus.fortran.ASTVisitor;
import ee.olegus.fortran.XMLGenerator;

/**
 * @author olegus
 *
 */
public class AllocateStatement extends Statement implements XMLGenerator {
	
	public enum Type {
		ALLOCATE,
		DEALLOCATE
	}
	
	private Type type;
	private List<DataReference> designators;
	
	public AllocateStatement(Type type) {
		this.type = type;
	}
	public List<DataReference> getDesignators() {
		return designators;
	}
	public void setDesignators(List<DataReference> designators) {
		this.designators = designators;
	}
	public Type getType() {
		return type;
	}
	public void setType(Type type) {
		this.type = type;
	}
	public Object astWalk(ASTVisitor visitor) {
		for(DataReference data: designators) {
			data.astWalk(visitor);
			visitor.visit(data);
		}
		
		return visitor.visit(this);
	}
	@Override
	public void generateXML(ContentHandler handler) throws SAXException {
		AttributesImpl attrs = new AttributesImpl();
		attrs.addAttribute("", "", "type", "", type.name().toLowerCase());
		handler.startElement("", "", "statement", attrs);
		super.generateXML(handler);
		
		for(DataReference dataReference: designators) {
			handler.startElement("", "", "designator", null);
			dataReference.generateXML(handler);
			handler.endElement("", "", "designator");
		}
		handler.endElement("", "", "statement");
	}
}
