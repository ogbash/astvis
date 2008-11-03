/**
 * 
 */
package ee.olegus.fortran.ast;

import java.util.ArrayList;
import java.util.List;

import ee.olegus.fortran.ASTVisitor;

/**
 * Statements that declare attributes like allocatable, dimension and pointer.
 * 
 * @author olegus
 *
 */
public class AttributeDeclaration extends Declaration {
	
	private Attribute attribute;
	private List<Entity> entities = new ArrayList<Entity>(2);
	
	public List<Entity> getEntities() {
		return entities;
	}

	public void setEntities(List<Entity> entities) {
		this.entities = entities;
	}

	public AttributeDeclaration(Attribute.Type type) {
		attribute = new Attribute(type);
	}

	public Attribute getAttribute() {
		return attribute;
	}

	public void setAttribute(Attribute attribute) {
		this.attribute = attribute;
	}

	/* (non-Javadoc)
	 * @see ee.olegus.fortran.ASTVisitable#astWalk(ee.olegus.fortran.ASTVisitor)
	 */
	public Object astWalk(ASTVisitor visitor) {
		// TODO Auto-generated method stub
		return this;
	}

	@Override
	public String toString() {
		return "AttributeDeclaration "+attribute;
	}
}
