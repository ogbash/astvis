/**
 * 
 */
package ee.olegus.fortran.ast;

import java.util.List;

/**
 * Variable attribute.
 * @author olegus
 *
 */
public class Attribute {
	public enum Type {
		PARAMETER,
		POINTER,
		ALLOCATABLE,
		DIMENSION,
		INTENT,
		OPTIONAL,
		EXTERNAL,
		TARGET,
		SAVE,
		PRIVATE,
		PUBLIC,
		PROTECTED
	}
	
	public enum IntentType {
		IN,
		OUT,
		INOUT
	}
	
	private Type type;
	private IntentType intent;
	private List<ArraySpecificationElement> arraySpecification;
	
	public Attribute(Type type) {
		this.type = type;
	}

	public String toString() {
		return type.name();
	}

	public List<ArraySpecificationElement> getArraySpecification() {
		return arraySpecification;
	}

	public void setArraySpecification(
			List<ArraySpecificationElement> arraySpecification) {
		this.arraySpecification = arraySpecification;
	}

	public Type getType() {
		return type;
	}

	public IntentType getIntent() {
		return intent;
	}

	public void setIntent(IntentType intent) {
		this.intent = intent;
	}	
}
