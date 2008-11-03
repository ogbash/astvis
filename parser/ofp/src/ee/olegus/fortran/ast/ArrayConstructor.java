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
public class ArrayConstructor extends Expression {

	private List<Expression> values;
	
	public ArrayConstructor(List<Expression> elements) {
		values = elements;
	}

	public ArrayConstructor() {
	}

	/* (non-Javadoc)
	 * @see ee.olegus.fortran.ast.TypeShape#getDimensions()
	 */
	public int getDimensions() {
		// TODO Auto-generated method stub
		return 0;
	}

	/* (non-Javadoc)
	 * @see ee.olegus.fortran.ast.TypeShape#getType()
	 */
	public Type getType() {
		// TODO Auto-generated method stub
		return null;
	}

	/* (non-Javadoc)
	 * @see ee.olegus.fortran.ast.TypeShape#hasAttribute(ee.olegus.fortran.ast.Attribute.Type)
	 */
	public boolean hasAttribute(ee.olegus.fortran.ast.Attribute.Type type) {
		// TODO Auto-generated method stub
		return false;
	}

	public List<Expression> getValues() {
		return values;
	}

	public void setValues(List<Expression> values) {
		this.values = values;
	}

	public Object astWalk(ASTVisitor visitor) {
		for(int i=0; i<values.size(); i++) {
			Expression expr = values.get(i);
			values.set(i, (Expression) expr.astWalk(visitor));
		}
		
		return this;
	}

}
