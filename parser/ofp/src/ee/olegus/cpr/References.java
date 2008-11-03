/**
 * 
 */
package ee.olegus.cpr;

import java.util.HashSet;
import java.util.Set;

import ee.olegus.fortran.ast.Call;
import ee.olegus.fortran.ast.Callable;
import ee.olegus.fortran.ast.Code;
import ee.olegus.fortran.ast.text.Locatable;

/**
 * @author olegus
 *
 */
public class References {
	private Callable callable;
	private Set<Call> calls = new HashSet<Call>();
	
	public References(Callable callable) {
		super();
		this.callable = callable;
	}

	public Callable getCallable() {
		return callable;
	}

	public Set<Call> getCalls() {
		return calls;
	}

	@Override
	public String toString() {
		StringBuffer str = new StringBuffer();
		if(callable != null)
			str.append("* "+callable.getName());
		else
			str.append("* <unknown>");
			
		for(Call call: calls) {
			Code code = ((Locatable)call).getLocation().code;
			str.append("  <-"+code.getFullName());
		}
		return str.toString();
	}
}
