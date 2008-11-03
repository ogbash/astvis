/**
 * 
 */
package ee.olegus.fortran.ast;

import java.util.List;

import ee.olegus.fortran.ASTVisitor;

/**
 * @author olegus
 *
 */
public class IntentStatement extends Declaration {
	private Attribute.IntentType intentType;
	private List<String> entities;
	
	public List<String> getEntities() {
		return entities;
	}
	public void setEntities(List<String> entities) {
		this.entities = entities;
	}
	public Attribute.IntentType getIntentType() {
		return intentType;
	}
	public void setIntentType(Attribute.IntentType intentType) {
		this.intentType = intentType;
	}
	public Object astWalk(ASTVisitor visitor) {
		return visitor.visit(this);
	}
}
