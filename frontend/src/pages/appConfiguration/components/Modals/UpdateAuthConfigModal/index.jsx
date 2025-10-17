import React from "react";
import { useDispatch, useSelector } from "react-redux";
import Modal from "../../../../../components/Modal";
import { selectAppConfiguration, toggleUpdateAuthConfigModal } from "../../../slice";
import UpdateAuthConfigForm from "./UpdateAuthConfigForm";

const UpdateAuthConfigModal = () => {
	const dispatch = useDispatch();
	const { isUpdateAuthConfigModalOpen } = useSelector(selectAppConfiguration);

	const handleClose = () => {
		dispatch(toggleUpdateAuthConfigModal());
	};

	return (
		<Modal
			label="Update Authentication Configuration"
			show={isUpdateAuthConfigModalOpen}
			closeModal={handleClose}
			ModalBody={<UpdateAuthConfigForm closeModal={handleClose} />}
		/>
	);
};

export default UpdateAuthConfigModal;