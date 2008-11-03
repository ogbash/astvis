/**
 * 
 */
package ee.olegus.fortran.ast;

import org.xml.sax.ContentHandler;
import org.xml.sax.SAXException;
import org.xml.sax.helpers.AttributesImpl;

import ee.olegus.fortran.XMLGenerator;

/**
 * @author olegus
 *
 */
public class ActualArgument extends Subscript {

	/**
	 * Argument name in case of named parameter. 
	 */
	private String name;
	
	public ActualArgument(Expression expression) {
		super(expression);
	}

	public ActualArgument(Subscript subscript) {
		super(subscript.getExpression());
	}

	public String getName() {
		return name;
	}

	public void setName(String name) {
		this.name = name;
	}

	@Override
	public void generateXML(ContentHandler handler) throws SAXException {
		AttributesImpl attrs = new AttributesImpl();
		
		if(name!=null)
			attrs.addAttribute("", "", "name", "", name);
		handler.startElement("", "", "argument", attrs);
		if(expression instanceof XMLGenerator) {
			((XMLGenerator)expression).generateXML(handler);
		}
		handler.endElement("", "", "argument");			
	}
}
