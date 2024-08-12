import { Menu, Transition } from '@headlessui/react';
import { Fragment, useState } from 'react';
import { usePopper } from 'react-popper';
import { ReactComponent as InfoIcon } from '../../../src/assets/images/svg/info-icon.svg';

export default function HeaderInfoHover({ message }) {
  const [referenceElement, setReferenceElement] = useState(null);
  const [popperElement, setPopperElement] = useState(null);
  const [isOpen, setIsOpen] = useState(false);

  const { styles, attributes } = usePopper(referenceElement, popperElement, {
    placement: 'bottom-end',
    modifiers: [
      {
        name: 'offset',
        options: {
          offset: [0, 8],
        },
      },
    ],
  });

  return (
    <div
      className="relative z-50 "
      onMouseEnter={() => setIsOpen(true)}
      onMouseLeave={() => setIsOpen(false)}
    >
      <Menu as="div" className="relative flex ">
        <Menu.Button
          className="flex w-full justify-center focus:outline-none z-0 relative"
          ref={(ref) => setReferenceElement(ref)}
        >
          <InfoIcon className="h-[16px] z-0 min-h-[16px] w-[16px] min-w-[16px] absolute bg-black" />
        </Menu.Button>
        <Transition
          as={Fragment}
          // @ts-ignore
          ref={(ref) => setPopperElement(ref)}
          style={styles.popper}
          {...attributes.popper}
          show={isOpen}  // Conditionally render based on state
        >
          <Menu.Items className="absolute right-0 top-[30px] min-w-[186px] origin-top-right rounded-[4px] bg-white shadow-table-menu focus:outline-none">
            <div className="p-[4px]">
              <Menu.Item>
                {({ active }) => (
                  <div
                    className={`${
                      active ? 'bg-white' : ''
                    } flex w-full max-w-fit flex-col rounded-[2px] px-[12px] py-[8px]`}
                  >
                    <span className="text-wrap text-start font-lato text-[12px] leading-[16px] z-50 tracking-[0.2px] text-[#6C747D]">
                      {message}
                    </span>
                  </div>
                )}
              </Menu.Item>
            </div>
          </Menu.Items>
        </Transition>
      </Menu>
    </div>
  );
}
