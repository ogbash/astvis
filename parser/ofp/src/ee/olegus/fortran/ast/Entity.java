/**
 * 
 */
package ee.olegus.fortran.ast;

import java.util.List;

import org.xml.sax.ContentHandler;
import org.xml.sax.SAXException;

import ee.olegus.fortran.XMLGenerator;


/**
 * @author olegus
 *
 */
public class Entity implements XMLGenerator {
	private String name;
	private Expression initialization;
	private List<ArraySpecificationElement> arraySpecification;

	public Entity(String id) {
		name = id;
	}

	public Expression getInitialization() {
		return initialization;
	}

	public void setInitialization(Expression initialization) {
		this.initialization = initialization;
	}

	public String getName() {
		return name;
	}

	public void setName(String name) {
		this.name = name;
	}

	@Override
	public String toString() {
		return name;
	}

	public List<ArraySpecificationElement> getArraySpecification() {
		return arraySpecification;
	}

	public void setArraySpecification(
			List<ArraySpecificationElement> arraySpecification) {
		this.arraySpecification = arraySpecification;
	}

	public void generateXML(ContentHandler handler) throws SAXException {
		handler.startElement("", "", "entity", null);
		
		handler.startElement("", "", "name", null);
		handler.characters(name.toCharArray(), 0, name.length());
		handler.endElement("", "", "name");
		
		handler.endElement("", "", "entity");
	}
}
