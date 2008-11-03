/**
 * 
 */
package ee.olegus.fortran.ast;

import org.xml.sax.ContentHandler;
import org.xml.sax.SAXException;

import ee.olegus.fortran.XMLGenerator;
import ee.olegus.fortran.ast.text.Locatable;
import ee.olegus.fortran.ast.text.Location;

/**
 * @author olegus
 *
 */
public class TypeSpecification implements XMLGenerator, Locatable {
	public enum Intrinsic {
		INTEGER,
		LOGICAL,
		REAL,
		COMPLEX, 
		CHARACTER,
		DOUBLEPRECISION, 
		DOUBLECOMPLEX
	}
	
	private String typeName;
	private Expression kind;
	private Location location;
	
	public TypeSpecification(String typeName) {
		this.typeName = typeName;
	}
	
	public Expression getKind() {
		return kind;
	}
	public void setKind(Expression kind) {
		this.kind = kind;
	}
	public String getTypeName() {
		return typeName;
	}
	public void setTypeName(String typeName) {
		this.typeName = typeName;
	}

	@Override
	public String toString() {
		return typeName;
	}

	public void generateXML(ContentHandler handler) throws SAXException {
		handler.startElement("", "", "type", null);
		handler.startElement("", "", "name", null);
		handler.characters(typeName.toCharArray(), 0, typeName.length());
		handler.endElement("", "", "name");
		
		if(kind instanceof XMLGenerator) {
			handler.startElement("", "", "kind", null);
			((XMLGenerator)kind).generateXML(handler);
			handler.endElement("", "", "kind");
		}
		handler.endElement("", "", "type");
	}

	public Location getLocation() {
		if(location==null)
			location = new Location();
		return location;
	}
}
