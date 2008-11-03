/**
 * 
 */
package ee.olegus.fortran.ast;

/**
 * @author olegus
 *
 */
public class ArraySpecificationElement {
	public enum Type {
		EXPR,
		EXPR_COLON,
		EXPR_COLON_EXPR,
		EXPR_COLON_ASTERISK,
		ASTERISK,
		COLON
	}

	private Type type;
	private Expression first;
	private Expression last;
	
	public ArraySpecificationElement(Type type) {
		this.type = type;
	}

	public Expression getFirst() {
		return first;
	}

	public void setFirst(Expression first) {
		this.first = first;
	}

	public Type getType() {
		return type;
	}

	public void setFirstType(Type type) {
		this.type = type;
	}

	public Expression getLast() {
		return last;
	}

	public void setLast(Expression last) {
		this.last = last;
	}

	
}
