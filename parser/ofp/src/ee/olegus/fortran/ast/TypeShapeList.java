/**
 * 
 */
package ee.olegus.fortran.ast;

import java.util.ArrayList;
import java.util.List;

/**
 * @author olegus
 *
 */
public class TypeShapeList extends ArrayList<TypeShape> {

	private static final long serialVersionUID = 1L;

	public TypeShapeList(List<? extends TypeShape> arguments) {
		super(arguments);
	}

	public TypeShapeList(int i) {
		super(i);
	}
	
	@SuppressWarnings("unchecked")
	@Override
	public boolean equals(Object obj) {
		if(!(obj instanceof List))
			return false;
		
		List<TypeShape> list = (List<TypeShape>) obj;
		if(list.size() != size())
			return false;
		
		for(int i=0; i<size(); i++) {
			if(!equalsTypeShape(get(i), list.get(i)))
				return false;
		}
		
		return true;
	}

	private boolean equalsTypeShape(TypeShape shape1, TypeShape shape2) {
		return shape1.getDimensions() == shape2.getDimensions() &&
			shape1.getType().equals(shape2.getType());
	}

}
