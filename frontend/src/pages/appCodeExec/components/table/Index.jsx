import './Index.css';
import RowMenu from './RowMenu';

export default function CodeExecTable({ data, onEdit, onExecute, onViewHistory }) {

	return (
		<div className="codeexec-table-wrapper">
			<table className="codeexec-table">
				<thead>
					<tr>
						<th>ID</th>
						<th>Name</th>
						<th>Description</th>
						<th>Created At</th>
						<th>Author</th>
						<th>Actions</th>
					</tr>
				</thead>
				<tbody>
					{data.map((item) => {
						return (
							<tr key={item.id}>
								<td className="id-cell">
									<code>{item.slug_code?.substring(0, 8)}...</code>
								</td>
								<td className="name-cell">{item.name}</td>
								<td className="description-cell">
									{item.description || '-'}
								</td>
								<td className="date-cell">
									{item.created_at || '-'}
								</td>
								<td className="creator-cell">
									{item.author_name || '-'}
								</td>
								<td className="actions-cell">
									<RowMenu
										codeexec={item}
										onEdit={() => onEdit(item)}
										onExecute={() => onExecute(item)}
										onViewHistory={() => onViewHistory(item)}
									/>
								</td>
							</tr>
						);
					})}
				</tbody>
			</table>
		</div>
	);
}
