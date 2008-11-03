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
public class AccessStatement extends Declaration {
	private Attribute.Type type;
	private List<String> names;

	public Attribute.Type getType() {
		return type;
	}

	public void setType(Attribute.Type type) {
		this.type = type;
	}

	public List<String> getNames() {
		return names;
	}

	public void setNames(List<String> names) {
		this.names = names;
	}

	public Object astWalk(ASTVisitor visitor) {
		return this;
	}
}
