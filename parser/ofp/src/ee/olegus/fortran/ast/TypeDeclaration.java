/**
 * 
 */
package ee.olegus.fortran.ast;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

import org.xml.sax.ContentHandler;
import org.xml.sax.SAXException;
import org.xml.sax.helpers.AttributesImpl;

import ee.olegus.fortran.ASTVisitor;
import ee.olegus.fortran.XMLGenerator;

/**
 * Declaration of variable types.
 * 
 * @author olegus
 *
 */
public class TypeDeclaration extends Declaration implements XMLGenerator {
	
	private TypeSpecification typeSpecification;
	private Set<Attribute> attributes = new HashSet<Attribute>(4);
	private List<Entity> entities = new ArrayList<Entity>(2);
	
	public Set<Attribute> getAttributes() {
		return attributes;
	}
	public void setAttributes(Set<Attribute> attributes) {
		this.attributes = attributes;
	}
	public List<Entity> getEntities() {
		return entities;
	}
	public void setEntities(List<Entity> entities) {
		this.entities = entities;
	}
	public TypeSpecification getTypeSpecification() {
		return typeSpecification;
	}
	public void setTypeSpecification(TypeSpecification typeSpecification) {
		this.typeSpecification = typeSpecification;
	}
	@Override
	public String toString() {
		return typeSpecification+" :: "+ entities;
	}
	public Object astWalk(ASTVisitor visitor) {
		return visitor.visit(this);
	}
	public void generateXML(ContentHandler handler) throws SAXException {
		AttributesImpl attrs = new AttributesImpl();
		attrs.addAttribute("", "", "type", "", "type");
		handler.startElement("", "", "declaration", attrs);
		
		super.generateXML(handler);

		// attibutes
		for(Attribute attribute: attributes) {
			attribute.generateXML(handler);
		}
		
		typeSpecification.generateXML(handler);
		
		// entities
		if(entities != null && entities.size()>0) {
			attrs.clear();
			attrs.addAttribute("", "", "count", "", ""+entities.size());
			handler.startElement("", "", "entities", attrs);
			for(Entity entity: entities) {
				entity.generateXML(handler);
			}
			handler.endElement("", "", "entities");
		}
		
		handler.endElement("", "", "declaration");		
	}
}
