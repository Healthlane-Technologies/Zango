import React, { useState, useEffect } from "react";
import ReactDOM from "react-dom";

const SAMLProviderModal = ({ isOpen, onClose, onSave, initialData = null }) => {
    const defaultFormData = {
        label: "",
        is_strict: false,
        is_debug_true: false,
        sp_entityId: "",
        sp_acsURL: "",
        sp_slo: "",
        sp_x509cert: "",
        sp_privatekey: "",
        idp_entityId: "",
        idp_sso: "",
        idp_slo: "",
        idp_x509cert: "",
        security_nameIdEncrypted: false,
        security_authnRequestsSigned: false,
        security_logoutRequestSigned: false,
        security_logoutResponseSigned: false,
        security_signMetadata: false,
        security_wantMessagesSigned: false,
        security_wantAssertionsSigned: false,
        security_wantAssertionsEncrypted: false,
        security_wantNameId: true,
        security_wantNameIdEncrypted: false,
        security_wantAttributeStatement: true,
        security_rejectUnsolicitedResponsesWithInResponseTo: false,
        security_requestedAuthnContext: true,
        security_requestedAuthnContextComparison: "exact",
        security_signatureAlgorithm: "http://www.w3.org/2000/09/xmldsig#rsa-sha1",
        security_digestAlgorithm: "http://www.w3.org/2000/09/xmldsig#sha1",
        name_id_format: "urn:oasis:names:tc:SAML:1.1:nameid-format:unspecified",
        is_active: true,
    };

    const [formData, setFormData] = useState(initialData ? { ...initialData } : defaultFormData);

    const [activeTab, setActiveTab] = useState("basic");
    const [errors, setErrors] = useState({});
    const [isLoading, setIsLoading] = useState(false);

    // Update form data when initialData changes (e.g., when editing)
    useEffect(() => {
        if (initialData) {
            setFormData({ ...initialData });
        } else {
            setFormData(defaultFormData);
        }
        setErrors({});
        setActiveTab("basic");
    }, [initialData]);

    const handleInputChange = (e) => {
        const { name, value, type, checked } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: type === "checkbox" ? checked : value,
        }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setIsLoading(true);
        try {
            // Validate required fields
            const requiredFields = [
                "label",
                "sp_entityId",
                "sp_acsURL",
                "idp_entityId",
                "idp_sso",
                "idp_x509cert",
            ];

            const newErrors = {};
            requiredFields.forEach(field => {
                if (!formData[field] || formData[field].trim() === "") {
                    newErrors[field] = "This field is required";
                }
            });

            if (Object.keys(newErrors).length > 0) {
                setErrors(newErrors);
                return;
            }

            setErrors({});
            if (onSave) {
                await onSave(formData);
            }
            onClose();
            // Refresh the page after successful save
            window.location.reload();
        } catch (error) {
            setErrors({ general: error.message });
        } finally {
            setIsLoading(false);
        }
    };

    const modalContent = (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-[16px] shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
                {/* Modal Header */}
                <div className="sticky top-0 bg-white border-b border-[#E5E7EB] p-[24px] flex items-center justify-between">
                    <div>
                        <h2 className="font-source-sans-pro text-[20px] font-bold leading-[28px] text-[#111827]">
                            {initialData ? 'Edit SAML Provider' : 'Configure SAML Provider'}
                        </h2>
                        <p className="font-lato text-[13px] text-[#6B7280] mt-[4px]">
                            {initialData ? 'Update SAML authentication provider settings' : 'Set up a new SAML authentication provider'}
                        </p>
                    </div>
                    <button
                        onClick={onClose}
                        className="text-[#6B7280] hover:text-[#111827] transition-colors"
                    >
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M18 6L6 18M6 6L18 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                        </svg>
                    </button>
                </div>

                {/* Modal Content */}
                <form onSubmit={handleSubmit} className="p-[24px]">
                    {/* Tabs */}
                    <div className="flex gap-[8px] mb-[24px] border-b border-[#E5E7EB]">
                        {["basic", "idp", "sp", "security"].map(tab => (
                            <button
                                key={tab}
                                type="button"
                                onClick={() => setActiveTab(tab)}
                                className={`px-[16px] py-[12px] font-medium text-[14px] border-b-2 transition-colors ${
                                    activeTab === tab
                                        ? "border-[#5048ED] text-[#5048ED]"
                                        : "border-transparent text-[#6B7280] hover:text-[#111827]"
                                }`}
                            >
                                {tab.charAt(0).toUpperCase() + tab.slice(1)}
                            </button>
                        ))}
                    </div>

                    {/* Basic Information Tab */}
                    {activeTab === "basic" && (
                        <div className="space-y-[16px]">
                            <div>
                                <label className="block font-lato text-[13px] font-semibold text-[#111827] mb-[6px]">
                                    Provider Label *
                                </label>
                                <input
                                    type="text"
                                    name="label"
                                    value={formData.label}
                                    onChange={handleInputChange}
                                    placeholder="e.g., Company SAML"
                                    className={`w-full px-[12px] py-[10px] rounded-[8px] border text-[13px] focus:outline-none focus:ring-2 focus:ring-[#5048ED] ${
                                        errors.label ? "border-[#EF4444]" : "border-[#E5E7EB]"
                                    }`}
                                />
                                {errors.label && <p className="text-[#EF4444] text-[12px] mt-[4px]">{errors.label}</p>}
                            </div>

                            <div className="grid grid-cols-2 gap-[12px]">
                                <label className="flex items-center gap-[8px] cursor-pointer">
                                    <input
                                        type="checkbox"
                                        name="is_strict"
                                        checked={formData.is_strict}
                                        onChange={handleInputChange}
                                        className="w-4 h-4 rounded border-[#E5E7EB]"
                                    />
                                    <span className="font-lato text-[13px] text-[#111827]">Strict Mode</span>
                                </label>

                                <label className="flex items-center gap-[8px] cursor-pointer">
                                    <input
                                        type="checkbox"
                                        name="is_debug_true"
                                        checked={formData.is_debug_true}
                                        onChange={handleInputChange}
                                        className="w-4 h-4 rounded border-[#E5E7EB]"
                                    />
                                    <span className="font-lato text-[13px] text-[#111827]">Debug Mode</span>
                                </label>
                            </div>

                            <label className="flex items-center gap-[8px] cursor-pointer">
                                <input
                                    type="checkbox"
                                    name="is_active"
                                    checked={formData.is_active}
                                    onChange={handleInputChange}
                                    className="w-4 h-4 rounded border-[#E5E7EB]"
                                />
                                <span className="font-lato text-[13px] text-[#111827]">Active</span>
                            </label>
                        </div>
                    )}

                    {/* IDP Configuration Tab */}
                    {activeTab === "idp" && (
                        <div className="space-y-[16px]">
                            <div>
                                <label className="block font-lato text-[13px] font-semibold text-[#111827] mb-[6px]">
                                    IdP Entity ID *
                                </label>
                                <input
                                    type="url"
                                    name="idp_entityId"
                                    value={formData.idp_entityId}
                                    onChange={handleInputChange}
                                    placeholder="https://app.example.com/saml/metadata"
                                    className={`w-full px-[12px] py-[10px] rounded-[8px] border text-[13px] focus:outline-none focus:ring-2 focus:ring-[#5048ED] ${
                                        errors.idp_entityId ? "border-[#EF4444]" : "border-[#E5E7EB]"
                                    }`}
                                />
                                {errors.idp_entityId && <p className="text-[#EF4444] text-[12px] mt-[4px]">{errors.idp_entityId}</p>}
                            </div>

                            <div>
                                <label className="block font-lato text-[13px] font-semibold text-[#111827] mb-[6px]">
                                    IdP SSO URL *
                                </label>
                                <input
                                    type="url"
                                    name="idp_sso"
                                    value={formData.idp_sso}
                                    onChange={handleInputChange}
                                    placeholder="https://app.example.com/saml/sso"
                                    className={`w-full px-[12px] py-[10px] rounded-[8px] border text-[13px] focus:outline-none focus:ring-2 focus:ring-[#5048ED] ${
                                        errors.idp_sso ? "border-[#EF4444]" : "border-[#E5E7EB]"
                                    }`}
                                />
                                {errors.idp_sso && <p className="text-[#EF4444] text-[12px] mt-[4px]">{errors.idp_sso}</p>}
                            </div>

                            <div>
                                <label className="block font-lato text-[13px] font-semibold text-[#111827] mb-[6px]">
                                    IdP SLO URL (Optional)
                                </label>
                                <input
                                    type="url"
                                    name="idp_slo"
                                    value={formData.idp_slo}
                                    onChange={handleInputChange}
                                    placeholder="https://app.example.com/saml/slo"
                                    className="w-full px-[12px] py-[10px] rounded-[8px] border border-[#E5E7EB] text-[13px] focus:outline-none focus:ring-2 focus:ring-[#5048ED]"
                                />
                            </div>

                            <div>
                                <label className="block font-lato text-[13px] font-semibold text-[#111827] mb-[6px]">
                                    IdP x509 Certificate *
                                </label>
                                <textarea
                                    name="idp_x509cert"
                                    value={formData.idp_x509cert}
                                    onChange={handleInputChange}
                                    placeholder="-----BEGIN CERTIFICATE-----&#10;...&#10;-----END CERTIFICATE-----"
                                    rows="6"
                                    className={`w-full px-[12px] py-[10px] rounded-[8px] border text-[13px] focus:outline-none focus:ring-2 focus:ring-[#5048ED] font-mono ${
                                        errors.idp_x509cert ? "border-[#EF4444]" : "border-[#E5E7EB]"
                                    }`}
                                />
                                {errors.idp_x509cert && <p className="text-[#EF4444] text-[12px] mt-[4px]">{errors.idp_x509cert}</p>}
                            </div>
                        </div>
                    )}

                    {/* SP Configuration Tab */}
                    {activeTab === "sp" && (
                        <div className="space-y-[16px]">
                            <div>
                                <label className="block font-lato text-[13px] font-semibold text-[#111827] mb-[6px]">
                                    SP Entity ID *
                                </label>
                                <input
                                    type="url"
                                    name="sp_entityId"
                                    value={formData.sp_entityId}
                                    onChange={handleInputChange}
                                    placeholder="https://yourapp.com/metadata/"
                                    className={`w-full px-[12px] py-[10px] rounded-[8px] border text-[13px] focus:outline-none focus:ring-2 focus:ring-[#5048ED] ${
                                        errors.sp_entityId ? "border-[#EF4444]" : "border-[#E5E7EB]"
                                    }`}
                                />
                                {errors.sp_entityId && <p className="text-[#EF4444] text-[12px] mt-[4px]">{errors.sp_entityId}</p>}
                            </div>

                            <div>
                                <label className="block font-lato text-[13px] font-semibold text-[#111827] mb-[6px]">
                                    SP ACS URL *
                                </label>
                                <input
                                    type="url"
                                    name="sp_acsURL"
                                    value={formData.sp_acsURL}
                                    onChange={handleInputChange}
                                    placeholder="https://yourapp.com/acs/"
                                    className={`w-full px-[12px] py-[10px] rounded-[8px] border text-[13px] focus:outline-none focus:ring-2 focus:ring-[#5048ED] ${
                                        errors.sp_acsURL ? "border-[#EF4444]" : "border-[#E5E7EB]"
                                    }`}
                                />
                                {errors.sp_acsURL && <p className="text-[#EF4444] text-[12px] mt-[4px]">{errors.sp_acsURL}</p>}
                            </div>

                            <div>
                                <label className="block font-lato text-[13px] font-semibold text-[#111827] mb-[6px]">
                                    SP SLO URL (Optional)
                                </label>
                                <input
                                    type="url"
                                    name="sp_slo"
                                    value={formData.sp_slo}
                                    onChange={handleInputChange}
                                    placeholder="https://yourapp.com/slo/"
                                    className="w-full px-[12px] py-[10px] rounded-[8px] border border-[#E5E7EB] text-[13px] focus:outline-none focus:ring-2 focus:ring-[#5048ED]"
                                />
                            </div>

                            <div>
                                <label className="block font-lato text-[13px] font-semibold text-[#111827] mb-[6px]">
                                    SP x509 Certificate (Optional)
                                </label>
                                <textarea
                                    name="sp_x509cert"
                                    value={formData.sp_x509cert}
                                    onChange={handleInputChange}
                                    placeholder="-----BEGIN CERTIFICATE-----&#10;...&#10;-----END CERTIFICATE-----"
                                    rows="4"
                                    className="w-full px-[12px] py-[10px] rounded-[8px] border border-[#E5E7EB] text-[13px] focus:outline-none focus:ring-2 focus:ring-[#5048ED] font-mono"
                                />
                            </div>

                            <div>
                                <label className="block font-lato text-[13px] font-semibold text-[#111827] mb-[6px]">
                                    SP Private Key (Optional)
                                </label>
                                <textarea
                                    name="sp_privatekey"
                                    value={formData.sp_privatekey}
                                    onChange={handleInputChange}
                                    rows="4"
                                    className="w-full px-[12px] py-[10px] rounded-[8px] border border-[#E5E7EB] text-[13px] focus:outline-none focus:ring-2 focus:ring-[#5048ED] font-mono"
                                />
                            </div>
                        </div>
                    )}

                    {/* Security Settings Tab */}
                    {activeTab === "security" && (
                        <div className="space-y-[16px]">
                            <div className="grid grid-cols-2 gap-[12px]">
                                {[
                                    { name: "security_nameIdEncrypted", label: "NameID Encrypted" },
                                    { name: "security_authnRequestsSigned", label: "AuthN Requests Signed" },
                                    { name: "security_logoutRequestSigned", label: "Logout Request Signed" },
                                    { name: "security_logoutResponseSigned", label: "Logout Response Signed" },
                                    { name: "security_signMetadata", label: "Sign Metadata" },
                                    { name: "security_wantMessagesSigned", label: "Want Messages Signed" },
                                    { name: "security_wantAssertionsSigned", label: "Want Assertions Signed" },
                                    { name: "security_wantAssertionsEncrypted", label: "Want Assertions Encrypted" },
                                    { name: "security_wantNameId", label: "Want NameID" },
                                    { name: "security_wantNameIdEncrypted", label: "Want NameID Encrypted" },
                                    { name: "security_wantAttributeStatement", label: "Want Attribute Statement" },
                                    { name: "security_requestedAuthnContext", label: "Requested AuthN Context" },
                                    { name: "security_rejectUnsolicitedResponsesWithInResponseTo", label: "Reject Unsolicited Responses" },
                                ].map(({ name, label }) => (
                                    <label key={name} className="flex items-center gap-[8px] cursor-pointer">
                                        <input
                                            type="checkbox"
                                            name={name}
                                            checked={formData[name]}
                                            onChange={handleInputChange}
                                            className="w-4 h-4 rounded border-[#E5E7EB]"
                                        />
                                        <span className="font-lato text-[13px] text-[#111827]">{label}</span>
                                    </label>
                                ))}
                            </div>

                            <div>
                                <label className="block font-lato text-[13px] font-semibold text-[#111827] mb-[6px]">
                                    Signature Algorithm
                                </label>
                                <select
                                    name="security_signatureAlgorithm"
                                    value={formData.security_signatureAlgorithm}
                                    onChange={handleInputChange}
                                    className="w-full px-[12px] py-[10px] rounded-[8px] border border-[#E5E7EB] text-[13px] focus:outline-none focus:ring-2 focus:ring-[#5048ED]"
                                >
                                    <option value="http://www.w3.org/2000/09/xmldsig#rsa-sha1">RSA-SHA1</option>
                                    <option value="http://www.w3.org/2000/09/xmldsig#dsa-sha1">DSA-SHA1</option>
                                    <option value="http://www.w3.org/2001/04/xmldsig-more#rsa-sha256">RSA-SHA256</option>
                                    <option value="http://www.w3.org/2001/04/xmldsig-more#rsa-sha384">RSA-SHA384</option>
                                    <option value="http://www.w3.org/2001/04/xmldsig-more#rsa-sha512">RSA-SHA512</option>
                                </select>
                            </div>

                            <div>
                                <label className="block font-lato text-[13px] font-semibold text-[#111827] mb-[6px]">
                                    Digest Algorithm
                                </label>
                                <select
                                    name="security_digestAlgorithm"
                                    value={formData.security_digestAlgorithm}
                                    onChange={handleInputChange}
                                    className="w-full px-[12px] py-[10px] rounded-[8px] border border-[#E5E7EB] text-[13px] focus:outline-none focus:ring-2 focus:ring-[#5048ED]"
                                >
                                    <option value="http://www.w3.org/2000/09/xmldsig#sha1">SHA1</option>
                                    <option value="http://www.w3.org/2001/04/xmlenc#sha256">SHA256</option>
                                    <option value="http://www.w3.org/2001/04/xmldsig-more#sha384">SHA384</option>
                                    <option value="http://www.w3.org/2001/04/xmlenc#sha512">SHA512</option>
                                </select>
                            </div>

                            <div>
                                <label className="block font-lato text-[13px] font-semibold text-[#111827] mb-[6px]">
                                    AuthN Context Comparison
                                </label>
                                <select
                                    name="security_requestedAuthnContextComparison"
                                    value={formData.security_requestedAuthnContextComparison}
                                    onChange={handleInputChange}
                                    className="w-full px-[12px] py-[10px] rounded-[8px] border border-[#E5E7EB] text-[13px] focus:outline-none focus:ring-2 focus:ring-[#5048ED]"
                                >
                                    <option value="exact">Exact</option>
                                    <option value="minimum">Minimum</option>
                                    <option value="maximum">Maximum</option>
                                    <option value="better">Better</option>
                                </select>
                            </div>

                            <div>
                                <label className="block font-lato text-[13px] font-semibold text-[#111827] mb-[6px]">
                                    NameID Format
                                </label>
                                <input
                                    type="text"
                                    name="name_id_format"
                                    value={formData.name_id_format}
                                    onChange={handleInputChange}
                                    placeholder="urn:oasis:names:tc:SAML:1.1:nameid-format:unspecified"
                                    className="w-full px-[12px] py-[10px] rounded-[8px] border border-[#E5E7EB] text-[13px] focus:outline-none focus:ring-2 focus:ring-[#5048ED] font-mono"
                                />
                            </div>
                        </div>
                    )}

                    {/* Error Message */}
                    {errors.general && (
                        <div className="mt-[16px] p-[12px] bg-[#FEE2E2] border border-[#FECACA] rounded-[8px]">
                            <p className="font-lato text-[13px] text-[#991B1B]">{errors.general}</p>
                        </div>
                    )}
                </form>

                {/* Modal Footer */}
                <div className="sticky bottom-0 bg-white border-t border-[#E5E7EB] p-[24px] flex items-center justify-end gap-[12px]">
                    <button
                        onClick={onClose}
                        className="px-[16px] py-[10px] border border-[#E5E7EB] text-[#111827] rounded-[8px] hover:bg-[#F9FAFB] transition-colors font-medium text-[14px]"
                    >
                        Cancel
                    </button>
                    <button
                        onClick={handleSubmit}
                        disabled={isLoading}
                        className="px-[16px] py-[10px] bg-[#5048ED] text-white rounded-[8px] hover:bg-[#3D2BA1] disabled:opacity-50 transition-colors font-medium text-[14px] flex items-center gap-[8px]"
                    >
                        {isLoading ? (
                            <>
                                <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                    <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" opacity="0.25"/>
                                    <path d="M12 2a10 10 0 0 1 10 10" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                                </svg>
                                Saving...
                            </>
                        ) : (
                            initialData ? "Update Provider" : "Save Provider"
                        )}
                    </button>
                </div>
            </div>
        </div>
    );

    return isOpen ? ReactDOM.createPortal(modalContent, document.body) : null;
};

export default SAMLProviderModal;
