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
public class DataStatement extends Declaration {
	private List<DataReference> objects;
	private List<Object> values;

	public void setObjects(List<DataReference> newObjects) {
		this.objects = newObjects;
	}

	public void setValues(List<Object> newValues) {
		this.values = newValues;
	}

	public Object astWalk(ASTVisitor visitor) {
		return visitor.visit(this);
	}
}
