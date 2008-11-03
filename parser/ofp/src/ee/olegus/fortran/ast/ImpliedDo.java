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
public class ImpliedDo extends Expression {

	private DataReference variable;
	private Expression first;
	private Expression last;
	private Expression stride;
	
	private List<Expression> values;
	
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

	public Expression getFirst() {
		return first;
	}

	public void setFirst(Expression first) {
		this.first = first;
	}

	public Expression getLast() {
		return last;
	}

	public void setLast(Expression last) {
		this.last = last;
	}

	public Expression getStride() {
		return stride;
	}

	public void setStride(Expression stride) {
		this.stride = stride;
	}

	public List<Expression> getValues() {
		return values;
	}

	public void setValues(List<Expression> values) {
		this.values = values;
	}

	public DataReference getVariable() {
		return variable;
	}

	public void setVariable(DataReference variable) {
		this.variable = variable;
	}

	public Object astWalk(ASTVisitor visitor) {
		return visitor.visit(this);
	}

}
