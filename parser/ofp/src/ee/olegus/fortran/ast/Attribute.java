/**
 * 
 */
package ee.olegus.fortran.ast;

import java.util.List;
import org.xml.sax.helpers.AttributesImpl;
import org.xml.sax.ContentHandler;
import org.xml.sax.SAXException;
import ee.olegus.fortran.XMLGenerator;

/**
 * Variable attribute.
 * @author olegus
 *
 */
public class Attribute implements XMLGenerator {
	public enum Type {
		PARAMETER,
		POINTER,
		ALLOCATABLE,
		DIMENSION,
		INTENT,
		OPTIONAL,
		EXTERNAL,
		TARGET,
		SAVE,
		PRIVATE,
		PUBLIC,
		PROTECTED
	}
	
	public enum IntentType {
		IN,
		OUT,
		INOUT
	}
	
	private Type type;
	private IntentType intent;
	private List<ArraySpecificationElement> arraySpecification;
	
	public Attribute(Type type) {
		this.type = type;
	}

	public String toString() {
		return type.name();
	}

	public List<ArraySpecificationElement> getArraySpecification() {
		return arraySpecification;
	}

	public void setArraySpecification(
			List<ArraySpecificationElement> arraySpecification) {
		this.arraySpecification = arraySpecification;
	}

	public Type getType() {
		return type;
	}

	public IntentType getIntent() {
		return intent;
	}

	public void setIntent(IntentType intent) {
		this.intent = intent;
	}	

	public void generateXML(ContentHandler handler) throws SAXException {
		AttributesImpl attrs = new AttributesImpl();
		attrs.addAttribute("", "", "type", "", this.type.toString());
		if(this.type==Type.INTENT) {
			attrs.addAttribute("", "", "intent", "", this.intent.toString());
		}
		handler.startElement("", "", "attribute", attrs);
		handler.endElement("", "", "attribute");
	}
}
